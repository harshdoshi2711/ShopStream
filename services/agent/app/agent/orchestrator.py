# services/agent/app/agent/orchestrator.py

from sqlalchemy.orm import Session

from services.agent.app.agent.llm_client import LLMClient
from services.agent.app.agent.intent_router import route_intent


class ShopAgentOrchestrator:
    """
    Coordinates:
    - LLM intent classification
    - Tool routing
    - Structured response building
    """

    def __init__(self):
        self.llm = LLMClient()

    def handle_query(self, query: str, db: Session):
        intent = self.llm.classify_intent(query)

        routed = route_intent(
            intent=intent,
            query=query,
            db=db,
        )

        return {
            "answer": routed["answer"],
            "suggestions": [],
            "metadata": {
                "intent": intent,
                "result_count": len(routed["results"]),
            },
        }
