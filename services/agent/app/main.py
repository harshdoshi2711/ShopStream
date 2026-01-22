# services/agent/app/main.py

from fastapi import FastAPI

from common.config.logging import configure_logging
from services.agent.app.api.assist import router as assist_router

configure_logging()

app = FastAPI(title="ShopStream ShopAgent Service")

app.include_router(assist_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "shopagent",
    }
