# services/agent/app/api/assist.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from common.database.session import get_db
from services.agent.app.schemas.responses import AgentResponse
from services.agent.app.tools.products import get_trending_products

router = APIRouter(prefix="/ai", tags=["shopagent"])


@router.post("/assist", response_model=AgentResponse)
def assist(query: str, db: Session = Depends(get_db)):
    products = get_trending_products(db)

    return AgentResponse(
        answer="Here are some trending products.",
        suggestions=[p["name"] for p in products],
        metadata={
            "tool_used": "get_trending_products",
        },
    )
