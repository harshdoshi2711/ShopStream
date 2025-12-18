import time
import logging
import json

from common.database.session import SessionLocal
from common.messaging.redis_streams import publish_event
from services.orders.app.models.outbox import OutboxEvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("outbox_publisher")

STREAM_NAME = "order_events"


def publish_events():
    db = SessionLocal()

    events = (
        db.query(OutboxEvent)
        .filter(OutboxEvent.status == "PENDING")
        .order_by(OutboxEvent.id)
        .limit(10)
        .all()
    )

    for event in events:
        # 🔒 Normalize payload (handles legacy rows safely)
        payload = (
            event.payload
            if isinstance(event.payload, dict)
            else json.loads(event.payload)
        )

        publish_event(
            STREAM_NAME,
            {
                "type": event.event_type,
                **payload,
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
