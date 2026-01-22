# services/orders/app/consumer.py

import json
import redis
import logging

from sqlalchemy.orm import Session

from common.database.session import SessionLocal
from common.config.logging import configure_logging
from common.messaging.redis_streams import publish_event
from common.messaging.dead_letter import send_to_dlq

from services.orders.app.models.order import Order
from services.orders.app.models.processed_event import OrdersProcessedEvent

configure_logging()
logger = logging.getLogger("shopstream.orders.consumer")

INVENTORY_EVENTS_STREAM = "inventory_events"
PAYMENT_EVENTS_STREAM = "payment_events"
INVENTORY_COMMANDS_STREAM = "inventory_commands"

GROUP_NAME = "orders_group"
CONSUMER_NAME = "orders_1"


def handle_inventory_event(payload: dict, db: Session):
    order_id = payload["order_id"]
    event_type = payload["type"]
    correlation_id = payload.get("correlation_id", "-")

    logger.info(
        "Received inventory event",
        extra={
            "correlation_id": correlation_id,
            "order_id": order_id,
            "event_type": event_type,
        },
    )

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        logger.warning(
            "Order not found for inventory event",
            extra={"correlation_id": correlation_id, "order_id": order_id},
        )
        return

    if order.status in ("CANCELLED", "CONFIRMED"):
        logger.info(
            "Ignoring inventory event for terminal order",
            extra={
                "correlation_id": correlation_id,
                "order_id": order_id,
                "status": order.status,
            },
        )
        return

    if event_type == "InventoryReserved":
        order.status = "AWAITING_PAYMENT"
        db.commit()

        logger.info(
            "Order moved to AWAITING_PAYMENT",
            extra={"correlation_id": correlation_id, "order_id": order_id},
        )
        return

    if event_type == "InventoryFailed":
        order.status = "CANCELLED"
        db.commit()

        logger.warning(
            "Order cancelled due to inventory failure",
            extra={"correlation_id": correlation_id, "order_id": order_id},
        )
        return

    if event_type == "InventoryReleased":
        logger.info(
            "Inventory rollback acknowledged",
            extra={"correlation_id": correlation_id, "order_id": order_id},
        )
        return


def handle_payment_event(payload: dict, db: Session):
    order_id = payload["order_id"]
    event_type = payload["type"]
    correlation_id = payload.get("correlation_id", "-")

    logger.info(
        "Received payment event",
        extra={
            "correlation_id": correlation_id,
            "order_id": order_id,
            "event_type": event_type,
        },
    )

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        logger.warning(
            "Order not found for payment event",
            extra={"correlation_id": correlation_id, "order_id": order_id},
        )
        return

    if order.status in ("CANCELLED", "CONFIRMED"):
        logger.info(
            "Ignoring payment event for terminal order",
            extra={
                "correlation_id": correlation_id,
                "order_id": order_id,
                "status": order.status,
            },
        )
        return

    if event_type == "PaymentSucceeded":
        order.status = "CONFIRMED"
        db.commit()

        logger.info(
            "Order confirmed after payment",
            extra={"correlation_id": correlation_id, "order_id": order_id},
        )
        return

    if event_type == "PaymentFailed":
        order.status = "CANCELLED"
        db.commit()

        logger.warning(
            "Payment failed, cancelling order",
            extra={"correlation_id": correlation_id, "order_id": order_id},
        )

        publish_event(
            INVENTORY_COMMANDS_STREAM,
            {
                "type": "InventoryReleaseRequested",
                "correlation_id": correlation_id,
                "order_id": order_id,
                "product_id": order.product_id,
                "quantity": order.quantity,
                "reason": "Payment failed",
            },
        )


def run():
    redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

    for stream in (INVENTORY_EVENTS_STREAM, PAYMENT_EVENTS_STREAM):
        try:
            redis_client.xgroup_create(stream, GROUP_NAME, id="0", mkstream=True)
        except redis.exceptions.ResponseError:
            pass

    logger.info("Orders consumer started", extra={"correlation_id": "-"})

    while True:
        messages = redis_client.xreadgroup(
            GROUP_NAME,
            CONSUMER_NAME,
            streams={
                INVENTORY_EVENTS_STREAM: ">",
                PAYMENT_EVENTS_STREAM: ">",
            },
            count=1,
            block=5000,
        )

        if not messages:
            continue

        for stream_name, entries in messages:
            for message_id, fields in entries:
                payload = json.loads(fields["payload"])
                db = SessionLocal()

                try:
                    already_processed = (
                        db.query(OrdersProcessedEvent)
                        .filter_by(
                            stream_name=stream_name,
                            event_id=message_id,
                        )
                        .first()
                    )

                    if already_processed:
                        redis_client.xack(stream_name, GROUP_NAME, message_id)
                        continue

                    if stream_name == INVENTORY_EVENTS_STREAM:
                        handle_inventory_event(payload, db)
                    else:
                        handle_payment_event(payload, db)

                    db.add(
                        OrdersProcessedEvent(
                            stream_name=stream_name,
                            event_id=message_id,
                        )
                    )
                    db.commit()
                    redis_client.xack(stream_name, GROUP_NAME, message_id)

                except Exception as e:
                    db.rollback()

                    send_to_dlq(
                        source_stream=stream_name,
                        message_id=message_id,
                        payload=payload,
                        error=e,
                    )

                    redis_client.xack(stream_name, GROUP_NAME, message_id)

                finally:
                    db.close()


if __name__ == "__main__":
    run()
