# services/agent/app/agent/orchestrator.py

import logging
from sqlalchemy.orm import Session

from services.agent.app.agent.llm_client import LLMClient
from services.agent.app.agent.intent_router import route_intent

logger = logging.getLogger("shopstream.shopagent")


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
        logger.info(
            "ShopAgent request received",
            extra={"query": query},
        )

        intent = self.llm.classify_intent(query)

        if intent == "UNKNOWN":
            logger.warning(
                "ShopAgent using fallback intent",
                extra={"query": query},
            )

        logger.info(
            "ShopAgent intent classified",
            extra={
                "query": query,
                "intent": intent,
            },
        )

        routed = route_intent(
            intent=intent,
            query=query,
            db=db,
        )

        logger.info(
            "ShopAgent response ready",
            extra={
                "intent": intent,
                "result_count": len(routed["results"]),
            },
        )

        return {
            "answer": routed["answer"],
            "suggestions": [],
            "metadata": {
                "intent": intent,
                "result_count": len(routed["results"]),
            },
        }
