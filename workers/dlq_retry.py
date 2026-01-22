# workers/dlq_retry.py

import logging
from typing import Dict

from workers.celery_app import celery_app
from common.messaging.redis_streams import publish_event

logger = logging.getLogger("shopstream.dlq.retry")

MAX_RETRIES = 3


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": MAX_RETRIES},
)
def retry_dead_letter_event(self, dlq_event: Dict):
    source_stream = dlq_event["source_stream"]
    original_payload = dlq_event["original_payload"]

    retry_count = dlq_event.get("retry_count", 0) + 1

    if retry_count > MAX_RETRIES:
        logger.error(
            "DLQ event exceeded max retries",
            extra={
                "source_stream": source_stream,
                "retry_count": retry_count,
            },
        )
        return

    logger.info(
        "Retrying DLQ event",
        extra={
            "source_stream": source_stream,
            "retry_count": retry_count,
        },
    )

    publish_event(
        source_stream,
        {
            **original_payload,
            "retry_count": retry_count,
        },
    )
