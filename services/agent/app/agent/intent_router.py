# services/agent/app/agent/intent_router.py

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from services.agent.app.agent.context import ConversationContext
from services.agent.app.tools.products import (
    get_trending_products,
    get_products_by_filters,
)
from services.agent.app.tools.orders import (
    explain_order_status,
    suggest_alternatives,
)

SUPPORTED_INTENTS = {
    "TRENDING_PRODUCTS",
    "FILTER_PRODUCTS",
    "ORDER_STATUS",
    "SUGGEST_ALTERNATIVES",
}

SAFE_FALLBACK_MESSAGE = (
    "I'm not sure how to help with that yet, "
    "but I can help you browse products, check orders, "
    "or suggest alternatives."
)


def _extract_first_number(text: str) -> Optional[int]:
    digits = "".join(filter(str.isdigit, text))
    return int(digits) if digits else None


def _is_followup(query: str) -> bool:
    lowered = query.lower()
    return lowered in {
        "show more",
        "more",
        "continue",
        "next",
        "what else",
    }


def route_intent(
    intent: str,
    query: str,
    db: Session,
    context: ConversationContext,
) -> Dict[str, Any]:
    """
    Context-aware intent router.

    Rules:
    - Never mutates DB
    - Never raises
    - Uses bounded conversation context
    """

    # 🔁 FOLLOW-UP HANDLING
    if _is_followup(query) and context.last_intent:
        intent = context.last_intent

    # 🔐 UNKNOWN / UNSUPPORTED
    if intent not in SUPPORTED_INTENTS:
        return {
            "answer": SAFE_FALLBACK_MESSAGE,
            "results": [],
        }

    # 🧠 TRENDING
    if intent == "TRENDING_PRODUCTS":
        results = get_trending_products(db)

        filtered = [
            r for r in results
            if r.get("product_id") not in context.last_result_ids
        ]

        return {
            "answer": "Here are some trending products right now.",
            "results": filtered,
        }

    # 🧠 FILTERED SEARCH
    if intent == "FILTER_PRODUCTS":
        results = get_products_by_filters(db, query=query)

        filtered = [
            r for r in results
            if r.get("product_id") not in context.last_result_ids
        ]

        return {
            "answer": "Here are some products that match your preferences.",
            "results": filtered,
        }

    # 📦 ORDER STATUS
    if intent == "ORDER_STATUS":
        order_id = _extract_first_number(query)
        if order_id is None:
            return {
                "answer": "I couldn't determine which order you meant.",
                "results": [],
            }

        return {
            "answer": "Here’s what’s happening with your order.",
            "results": [explain_order_status(db, order_id)],
        }

    # 🔁 ALTERNATIVES
    if intent == "SUGGEST_ALTERNATIVES":
        product_id = _extract_first_number(query)
        if product_id is None:
            return {
                "answer": "I couldn't identify which product you’re referring to.",
                "results": [],
            }

        results = suggest_alternatives(db, product_id)

        filtered = [
            r for r in results
            if r.get("product_id") not in context.last_result_ids
        ]

        return {
            "answer": "Here are some alternatives you might like.",
            "results": filtered,
        }

    return {
        "answer": SAFE_FALLBACK_MESSAGE,
        "results": [],
    }
