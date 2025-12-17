# services/orders/app/main.py

from fastapi import FastAPI
# (remove this later):
from sqlalchemy import text

from common.config.logging import configure_logging
# (remove this later):
from common.database.session import engine
# (remove this later):
from common.messaging.redis_client import get_redis_client
from services.orders.app.api.orders import router as orders_router
from services.orders.app.ui.routes import router as ui_router

configure_logging()

app = FastAPI(title="ShopStream Orders Service")

app.include_router(orders_router)
app.include_router(ui_router)


@app.get("/health")
def health_check():
    # DB check (remove this later)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    # Redis check (remove this later)
    redis = get_redis_client()
    redis.ping()

    return {
        "status": "ok",
        "service": "orders",
    }
