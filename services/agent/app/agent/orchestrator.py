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
    Owns:
    - intent resolution (LLM + followups)
    - context updates
    - API response normalization
    """

    def __init__(self):
        self.llm = LLMClient()
        self.context = ConversationContext()

    def handle_query(
        self,
        query: str,
        db: Session,
    ) -> Dict[str, Any]:

        logger.info("ShopAgent received query", extra={"query": query})

        llm_intent = self.llm.classify_intent(query)

        logger.info(
            "LLM intent classified",
            extra={"llm_intent": llm_intent},
        )

        routed = route_intent(
            intent=llm_intent,
            query=query,
            db=db,
            context=self.context,
        )

        suggestions = routed.get("results", [])
        answer = routed.get("answer", "I'm not sure how to help with that.")

        # 🔑 CRITICAL FIX:
        # effective intent is what the router actually used
        effective_intent = (
            self.context.last_intent
            if llm_intent == "UNKNOWN" and self.context.last_intent
            else llm_intent
        )

        fallback_used = effective_intent == "UNKNOWN"

        # SINGLE SOURCE OF TRUTH: stable `id`
        result_ids = [
            item["id"]
            for item in suggestions
            if isinstance(item, dict) and "id" in item
        ]

        # 🔑 UPDATE CONTEXT WITH EFFECTIVE INTENT (NOT RAW LLM INTENT)
        self.context.update(
            intent=effective_intent,
            query=query,
            result_ids=result_ids,
        )

        logger.info(
            "ShopAgent response prepared",
            extra={
                "effective_intent": effective_intent,
                "result_count": len(suggestions),
                "fallback_used": fallback_used,
            },
        )

        return {
            "answer": answer,
            "suggestions": suggestions,
            "metadata": {
                "intent": effective_intent,
                "result_count": len(suggestions),
                "fallback_used": fallback_used,
            },
        }
