# workers/dlq_scanner.py

import json
import logging
import redis

from workers.celery_app import celery_app
from workers.dlq_retry import retry_dead_letter_event
from common.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger("shopstream.dlq.scanner")

DLQ_STREAM = "dead_letter_events"


def get_redis_client() -> redis.Redis:
    return redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        decode_responses=True,
    )


@celery_app.task
def scan_and_retry_dlq(limit: int = 10):
    redis_client = get_redis_client()

    events = redis_client.xrange(DLQ_STREAM, count=limit)

    if not events:
        logger.info("No DLQ events found")
        return

    for message_id, fields in events:
        payload = json.loads(fields["payload"])

        logger.info(
            "Submitting DLQ event for retry",
            extra={
                "source_stream": payload.get("source_stream"),
                "message_id": message_id,
            },
        )

        retry_dead_letter_event.delay(payload)
