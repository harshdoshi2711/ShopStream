# services/orders/app/consumer.py

import json
import redis
import logging

from sqlalchemy.orm import Session

from common.database.session import SessionLocal
from common.config.logging import configure_logging
from common.messaging.redis_streams import publish_event
from services.orders.app.models.order import Order
from services.orders.app.models.processed_event import OrdersProcessedEvent

configure_logging()
logger = logging.getLogger("shopstream.orders.consumer")

INVENTORY_EVENTS_STREAM = "inventory_events"
PAYMENT_EVENTS_STREAM = "payment_events"
PAYMENT_COMMANDS_STREAM = "payment_commands"
INVENTORY_COMMANDS_STREAM = "inventory_commands"

GROUP_NAME = "orders_group"
CONSUMER_NAME = "orders_1"


def handle_inventory_event(payload: dict, db: Session):
    correlation_id = payload.get("correlation_id", "-")
    order_id = payload["order_id"]
    event_type = payload["type"]

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return

    # 🛑 Terminal guard
    if order.status in ("CANCELLED", "CONFIRMED"):
        return

    if event_type == "InventoryReserved":
        order.status = "AWAITING_PAYMENT"
        db.commit()

        logger.info(
            "Inventory reserved, requesting payment",
            extra={
                "correlation_id": correlation_id,
                "order_id": order_id,
            },
        )

        # 🔑 COMMAND → Payments
        publish_event(
            PAYMENT_COMMANDS_STREAM,
            {
                "type": "PaymentRequested",
                "correlation_id": correlation_id,
                "order_id": order_id,
                "amount_due": float(order.total_price),
            },
        )
        return

    if event_type == "InventoryFailed":
        order.status = "CANCELLED"
        db.commit()

        logger.warning(
            "Inventory failed, cancelling order",
            extra={
                "correlation_id": correlation_id,
                "order_id": order_id,
            },
        )
        return

    if event_type == "InventoryReleased":
        logger.info(
            "Inventory rollback completed",
            extra={
                "correlation_id": correlation_id,
                "order_id": order_id,
            },
        )
        return


def handle_payment_event(payload: dict, db: Session):
    correlation_id = payload.get("correlation_id", "-")
    order_id = payload["order_id"]
    event_type = payload["type"]

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return

    # 🛑 Terminal guard
    if order.status in ("CANCELLED", "CONFIRMED"):
        return

    if event_type == "PaymentSucceeded":
        order.status = "CONFIRMED"
        db.commit()

        logger.info(
            "Order confirmed after successful payment",
            extra={
                "correlation_id": correlation_id,
                "order_id": order_id,
            },
        )
        return

    if event_type == "PaymentFailed":
        order.status = "CANCELLED"
        db.commit()

        logger.warning(
            "Payment failed, cancelling order",
            extra={
                "correlation_id": correlation_id,
                "order_id": order_id,
            },
        )

        # 🔑 COMMAND → Inventory
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
    redis_client = redis.Redis(
        host="redis",
        port=6379,
        decode_responses=True,
    )

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
                    if (
                        db.query(OrdersProcessedEvent)
                        .filter_by(
                            stream_name=stream_name,
                            event_id=message_id,
                        )
                        .first()
                    ):
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

                finally:
                    db.close()


if __name__ == "__main__":
    run()
