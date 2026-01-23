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
    - Deterministic response shaping
    """

    def __init__(self):
        self.llm = LLMClient()

    def handle_query(self, query: str, db: Session):
        logger.info(
            "ShopAgent request received",
            extra={"query": query},
        )

        intent = self.llm.classify_intent(query)
        fallback_used = False

        if intent == "UNKNOWN":
            fallback_used = True
            logger.warning(
                "ShopAgent fallback activated",
                extra={"query": query},
            )

        logger.info(
            "ShopAgent intent resolved",
            extra={
                "query": query,
                "intent": intent,
                "fallback_used": fallback_used,
            },
        )

        routed = route_intent(
            intent=intent,
            query=query,
            db=db,
        )

        response = {
            "answer": routed["answer"],
            "suggestions": [],
            "metadata": {
                "intent": intent,
                "result_count": len(routed["results"]),
                "fallback_used": fallback_used,
            },
        }

        logger.info(
            "ShopAgent response completed",
            extra={
                "intent": intent,
                "result_count": len(routed["results"]),
                "fallback_used": fallback_used,
            },
        )

        return response
