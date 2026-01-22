# services/agent/app/api/assist.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from common.database.session import get_db
from services.agent.app.schemas.responses import AgentResponse
from services.agent.app.agent.orchestrator import ShopAgentOrchestrator

router = APIRouter(prefix="/ai", tags=["shopagent"])

orchestrator = ShopAgentOrchestrator()


@router.post("/assist", response_model=AgentResponse)
def assist(query: str, db: Session = Depends(get_db)):
    response = orchestrator.handle_query(query, db)

    return AgentResponse(**response)
