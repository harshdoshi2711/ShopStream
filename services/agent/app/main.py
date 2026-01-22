# services/agent/app/main.py

import uuid
from fastapi import FastAPI, Request

from common.config.logging import configure_logging
from services.agent.app.api.assist import router as assist_router

configure_logging()

app = FastAPI(title="ShopAgent")


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    correlation_id = request.headers.get(
        "X-Correlation-ID", str(uuid.uuid4())
    )

    request.state.correlation_id = correlation_id

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


app.include_router(assist_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "shopagent",
    }
