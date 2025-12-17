# common/messaging/redis_streams.py

import json
from typing import Dict

from common.messaging.redis_client import get_redis_client


def publish_event(stream_name: str, data: Dict):
    """
    Publish a structured event to a Redis Stream.
    """
    redis = get_redis_client()

    redis.xadd(
        stream_name,
        {
            "type": data["type"],
            "payload": json.dumps(data),
        }
    )
