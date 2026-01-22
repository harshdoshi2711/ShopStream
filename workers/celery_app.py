# workers/celery_app.py

from celery import Celery
from celery.schedules import crontab
from common.config.settings import get_settings

settings = get_settings()

celery_app = Celery(
    "shopstream",
    broker=f"redis://{settings.redis_host}:{settings.redis_port}/0",
    backend=f"redis://{settings.redis_host}:{settings.redis_port}/1",
    include=[
        "workers.dlq_scanner",
        "workers.dlq_retry"
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

# 🔁 Periodic tasks
    beat_schedule={
        "retry-dead-letter-events-every-minute": {
            "task": "workers.dlq_scanner.scan_and_retry_dlq",
            "schedule": 60.0,
            "args": (),
        }
    },
)