# services/orders/app/consumer.py

import json
import redis
import logging

from sqlalchemy.orm import Session

from common.database.session import SessionLocal
from common.config.logging import configure_logging
from services.orders.app.models.order import Order
from services.orders.app.models.processed_event import OrdersProcessedEvent

configure_logging()
logger = logging.getLogger("shopstream.orders.consumer")

STREAM_NAME = "inventory_events"
GROUP_NAME = "orders_group"
CONSUMER_NAME = "orders_1"


def handle_inventory_event(payload: dict, db: Session):
    correlation_id = payload.get("correlation_id", "-")
    order_id = payload["order_id"]
    event_type = payload["type"]

    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        logger.warning(
            "Order not found for inventory event",
            extra={
                "correlation_id": correlation_id,
                "order_id": order_id,
                "event_type": event_type,
            },
        )
        return

    if event_type == "InventoryReserved":
        order.status = "CONFIRMED"

    elif event_type == "InventoryFailed":
        order.status = "CANCELLED"

    else:
        logger.warning(
            "Unknown inventory event type",
            extra={
                "correlation_id": correlation_id,
                "order_id": order_id,
                "event_type": event_type,
            },
        )
        return

    db.commit()

    logger.info(
        "Order status updated from inventory event",
        extra={
            "correlation_id": correlation_id,
            "order_id": order_id,
            "new_status": order.status,
        },
    )


def run():
    redis_client = redis.Redis(
        host="redis",
        port=6379,
        decode_responses=True,
    )

    try:
        redis_client.xgroup_create(
            STREAM_NAME,
            GROUP_NAME,
            id="0",
            mkstream=True,
        )
    except redis.exceptions.ResponseError:
        pass  # consumer group already exists

    while True:
        messages = redis_client.xreadgroup(
            GROUP_NAME,
            CONSUMER_NAME,
            streams={STREAM_NAME: ">"},
            count=1,
            block=5000,
        )

        if not messages:
            continue

        for _, entries in messages:
            for message_id, fields in entries:
                payload = json.loads(fields["payload"])
                event_id = message_id

                db = SessionLocal()
                try:
                    # 🔐 Idempotency check
                    already_processed = (
                        db.query(OrdersProcessedEvent)
                        .filter_by(event_id=event_id)
                        .first()
                    )

                    if already_processed:
                        logger.info(
                            "Duplicate inventory event ignored",
                            extra={
                                "correlation_id": payload.get("correlation_id", "-"),
                                "event_id": event_id,
                            },
                        )
                        redis_client.xack(STREAM_NAME, GROUP_NAME, message_id)
                        continue

                    handle_inventory_event(payload, db)

                    db.add(OrdersProcessedEvent(event_id=event_id))
                    db.commit()

                    redis_client.xack(STREAM_NAME, GROUP_NAME, message_id)

                finally:
                    db.close()


if __name__ == "__main__":
    run()
