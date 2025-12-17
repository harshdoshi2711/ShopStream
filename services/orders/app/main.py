# services/orders/app/main.py

from fastapi import FastAPI
from sqlalchemy import text

from common.config.logging import configure_logging
from common.database.session import engine
from common.messaging.redis_client import get_redis_client

configure_logging()

app = FastAPI(title="ShopStream Orders Service")


@app.get("/health")
def health_check():
    # DB check
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    # Redis check
    redis = get_redis_client()
    redis.ping()

    return {
        "status": "ok",
        "service": "orders",
    }
