# common/messaging/dead_letter.py

import logging
from datetime import datetime
from typing import Dict

from common.messaging.redis_streams import publish_event

logger = logging.getLogger("shopstream.dlq")

DLQ_STREAM = "dead_letter_events"


def send_to_dlq(
    *,
    source_stream: str,
    message_id: str,
    payload: Dict,
    error: Exception,
):
    """
    Publish a failed event to the Dead Letter Queue (Redis Stream).
    """
    dlq_payload = {
        "type": "DeadLetterEvent",
        "source_stream": source_stream,
        "message_id": message_id,
        "original_payload": payload,
        "error": str(error),
        "failed_at": datetime.utcnow().isoformat(),
    }

    publish_event(DLQ_STREAM, dlq_payload)

    logger.error(
        "Message sent to DLQ",
        extra={
            "source_stream": source_stream,
            "message_id": message_id,
            "error": str(error),
        },
    )
