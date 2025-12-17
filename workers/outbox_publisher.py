# workers/outbox_publisher.py

import time
import logging

from common.database.session import SessionLocal
from common.messaging.redis_client import get_redis_client
from services.orders.app.models.outbox import OutboxEvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("outbox_publisher")

STREAM_NAME = "order_events"


def publish_events():
    db = SessionLocal()
    redis = get_redis_client()

    events = (
        db.query(OutboxEvent)
        .filter(OutboxEvent.status == "PENDING")
        .order_by(OutboxEvent.id)
        .limit(10)
        .all()
    )

    for event in events:
        redis.xadd(
            STREAM_NAME,
            {
                "type": event.event_type,
                "payload": str(event.payload),
            },
        )
        event.status = "PUBLISHED"
        db.add(event)

    db.commit()
    db.close()


if __name__ == "__main__":
    while True:
        publish_events()
        time.sleep(2)
