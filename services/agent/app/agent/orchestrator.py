# services/agent/app/agent/orchestrator.py

import logging
from typing import Dict, Any
from sqlalchemy.orm import Session

from services.agent.app.agent.context import ConversationContext
from services.agent.app.agent.intent_router import route_intent
from services.agent.app.agent.llm_client import LLMClient

logger = logging.getLogger("shopstream.shopagent.orchestrator")


class ShopAgentOrchestrator:
    """
    Central coordinator for ShopAgent.

    Responsibilities:
    - LLM intent classification
    - Intent → tool routing
    - Response normalization (API contract enforcement)
    - Bounded context tracking (internal only)
    """

    def __init__(self):
        self.llm = LLMClient()
        self.context = ConversationContext()

    def handle_query(
        self,
        query: str,
        db: Session,
    ) -> Dict[str, Any]:

        logger.info(
            "ShopAgent received query",
            extra={"query": query},
        )

        intent = self.llm.classify_intent(query)

        logger.info(
            "Intent classified",
            extra={"intent": intent},
        )

        routed = route_intent(
            intent=intent,
            query=query,
            db=db,
        )

        # Normalize tool output
        suggestions = routed.get("results", [])
        answer = routed.get("answer", "I'm not sure how to help with that.")

        fallback_used = intent == "UNKNOWN"

        # Extract IDs for internal context only
        result_ids = []
        for item in suggestions:
            if isinstance(item, dict) and "id" in item:
                result_ids.append(item["id"])

        self.context.update(
            intent=intent,
            query=query,
            result_ids=result_ids,
        )

        logger.info(
            "ShopAgent response prepared",
            extra={
                "intent": intent,
                "result_count": len(suggestions),
                "fallback_used": fallback_used,
            },
        )

        # 🔒 FINAL API SHAPE — MUST MATCH AgentResponse EXACTLY
        return {
            "answer": answer,
            "suggestions": suggestions,
            "metadata": {
                "intent": intent,
                "result_count": len(suggestions),
                "fallback_used": fallback_used,
            },
        }
