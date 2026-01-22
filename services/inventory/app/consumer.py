# services/inventory/app/consumer.py

import json
import redis
import logging

from sqlalchemy.orm import Session

from common.database.session import SessionLocal
from common.config.logging import configure_logging
from common.messaging.redis_streams import publish_event
from common.messaging.dead_letter import send_to_dlq

from services.inventory.app.models.inventory import Inventory
from services.inventory.app.models.processed_event import InventoryProcessedEvent

configure_logging()
logger = logging.getLogger("shopstream.inventory")

ORDER_STREAM = "order_events"
INVENTORY_COMMANDS_STREAM = "inventory_commands"
INVENTORY_EVENTS_STREAM = "inventory_events"

GROUP_NAME = "inventory_group"
CONSUMER_NAME = "inventory_1"


def process_order_created(payload: dict, db: Session):
    order_id = payload["order_id"]
    product_id = payload["product_id"]
    quantity = payload["quantity"]
    correlation_id = payload.get("correlation_id", "-")

    logger.info(
        "Processing OrderCreated",
        extra={
            "correlation_id": correlation_id,
            "order_id": order_id,
            "product_id": product_id,
            "quantity": quantity,
        },
    )

    inventory = db.query(Inventory).filter_by(product_id=product_id).first()

    if not inventory or inventory.stock < quantity:
        logger.warning(
            "Inventory insufficient",
            extra={
                "correlation_id": correlation_id,
                "order_id": order_id,
                "product_id": product_id,
            },
        )

        publish_event(
            INVENTORY_EVENTS_STREAM,
            {
                "type": "InventoryFailed",
                "correlation_id": correlation_id,
                "order_id": order_id,
                "product_id": product_id,
                "reason": "Insufficient stock",
            },
        )
        return

    inventory.stock -= quantity
    db.commit()

    logger.info(
        "Inventory reserved",
        extra={
            "correlation_id": correlation_id,
            "order_id": order_id,
            "product_id": product_id,
            "remaining_stock": inventory.stock,
        },
    )

    publish_event(
        INVENTORY_EVENTS_STREAM,
        {
            "type": "InventoryReserved",
            "correlation_id": correlation_id,
            "order_id": order_id,
            "product_id": product_id,
            "quantity": quantity,
        },
    )


def process_inventory_release(payload: dict, db: Session):
    order_id = payload["order_id"]
    product_id = payload["product_id"]
    quantity = payload["quantity"]
    correlation_id = payload.get("correlation_id", "-")

    logger.info(
        "Processing InventoryReleaseRequested",
        extra={
            "correlation_id": correlation_id,
            "order_id": order_id,
            "product_id": product_id,
            "quantity": quantity,
        },
    )

    inventory = db.query(Inventory).filter_by(product_id=product_id).first()
    if not inventory:
        logger.error(
            "Inventory record not found during release",
            extra={
                "correlation_id": correlation_id,
                "order_id": order_id,
                "product_id": product_id,
            },
        )
        raise RuntimeError("Inventory record not found during release")

    inventory.stock += quantity
    db.commit()

    logger.info(
        "Inventory released",
        extra={
            "correlation_id": correlation_id,
            "order_id": order_id,
            "product_id": product_id,
            "current_stock": inventory.stock,
        },
    )

    publish_event(
        INVENTORY_EVENTS_STREAM,
        {
            "type": "InventoryReleased",
            "correlation_id": correlation_id,
            "order_id": order_id,
            "product_id": product_id,
            "quantity": quantity,
        },
    )


def run():
    redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

    for stream in (ORDER_STREAM, INVENTORY_COMMANDS_STREAM):
        try:
            redis_client.xgroup_create(stream, GROUP_NAME, id="0", mkstream=True)
        except redis.exceptions.ResponseError:
            pass

    logger.info("Inventory consumer started", extra={"correlation_id": "-"})

    while True:
        messages = redis_client.xreadgroup(
            GROUP_NAME,
            CONSUMER_NAME,
            streams={
                ORDER_STREAM: ">",
                INVENTORY_COMMANDS_STREAM: ">",
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
                        db.query(InventoryProcessedEvent)
                        .filter_by(stream_name=stream_name, event_id=message_id)
                        .first()
                    )

                    if already_processed:
                        redis_client.xack(stream_name, GROUP_NAME, message_id)
                        continue

                    if stream_name == ORDER_STREAM:
                        process_order_created(payload, db)
                    else:
                        process_inventory_release(payload, db)

                    db.add(
                        InventoryProcessedEvent(
                            stream_name=stream_name,
                            event_id=message_id,
                            order_id=payload.get("order_id"),
                            correlation_id=payload.get("correlation_id"),
                        )
                    )
                    db.commit()
                    redis_client.xack(stream_name, GROUP_NAME, message_id)

                except Exception as e:
                    db.rollback()

                    logger.exception(
                        "Unhandled error in inventory consumer",
                        extra={
                            "correlation_id": payload.get("correlation_id", "-"),
                            "stream_name": stream_name,
                            "event_id": message_id,
                        },
                    )

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
