# services/inventory/app/consumer.py

import json
import redis

from sqlalchemy.orm import Session

from common.database.session import SessionLocal
from services.inventory.app.models.inventory import Inventory
from common.messaging.redis_streams import publish_event

STREAM_NAME = "order_events"
GROUP_NAME = "inventory_group"
CONSUMER_NAME = "inventory_1"


def process_order_created(payload: dict, db: Session):
    order_id = payload["order_id"]
    product_id = payload["product_id"]
    quantity = payload["quantity"]

    inventory = db.query(Inventory).filter_by(product_id=product_id).first()

    if not inventory or inventory.stock < quantity:
        publish_event(
            "inventory_events",
            {
                "type": "InventoryFailed",
                "order_id": order_id,
                "product_id": product_id,
                "reason": "Insufficient stock",
            },
        )
        return

    inventory.stock -= quantity
    db.commit()

    publish_event(
        "inventory_events",
        {
            "type": "InventoryReserved",
            "order_id": order_id,
            "product_id": product_id,
            "quantity": quantity,
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
            STREAM_NAME, GROUP_NAME, id="0", mkstream=True
        )
    except redis.exceptions.ResponseError:
        pass

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
                payload = json.loads(fields["payload"])  # ✅ NOW VALID JSON

                db = SessionLocal()
                try:
                    process_order_created(payload, db)
                    redis_client.xack(STREAM_NAME, GROUP_NAME, message_id)
                finally:
                    db.close()


if __name__ == "__main__":
    run()
