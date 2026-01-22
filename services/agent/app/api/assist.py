# services/agent/app/api/assist.py

from fastapi import APIRouter
from services.agent.app.schemas.responses import AgentResponse

router = APIRouter(prefix="/ai", tags=["shopagent"])


@router.post("/assist", response_model=AgentResponse)
def assist(query: str):
    """
    Stub endpoint for ShopAgent.
    Real reasoning + tools will be added in later phases.
    """
    return AgentResponse(
        answer="ShopAgent is online, but reasoning is not enabled yet.",
        suggestions=[],
        metadata={
            "status": "stub",
        },
    )
