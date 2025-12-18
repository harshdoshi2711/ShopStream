# services/orders/app/consumer.py

import json
import redis
import logging

from sqlalchemy.orm import Session

from common.database.session import SessionLocal
from services.orders.app.models.order import Order

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("orders_consumer")

STREAM_NAME = "inventory_events"
GROUP_NAME = "orders_group"
CONSUMER_NAME = "orders_1"


def handle_inventory_event(payload: dict, db: Session):
    order_id = payload["order_id"]
    event_type = payload["type"]

    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        logger.warning(f"Order {order_id} not found")
        return

    if event_type == "InventoryReserved":
        order.status = "CONFIRMED"

    elif event_type == "InventoryFailed":
        order.status = "CANCELLED"

    else:
        logger.warning(f"Unknown inventory event: {event_type}")
        return

    db.commit()
    logger.info(f"Order {order_id} updated → {order.status}")


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
        pass  # group already exists

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

                db = SessionLocal()
                try:
                    handle_inventory_event(payload, db)
                    redis_client.xack(STREAM_NAME, GROUP_NAME, message_id)
                finally:
                    db.close()


if __name__ == "__main__":
    run()
