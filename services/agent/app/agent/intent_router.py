# services/agent/app/agent/intent_router.py
from typing import Dict, Any
from sqlalchemy.orm import Session

from services.agent.app.tools.products import (
    get_trending_products,
    get_products_by_filters,
)
from services.agent.app.tools.orders import (
    explain_order_status,
    suggest_alternatives,
)

# 🔒 Explicit, documented intent set
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


def _extract_first_number(text: str) -> int | None:
    """
    Extract the first integer found in the text.
    Returns None if no digits are present.
    """
    digits = "".join(filter(str.isdigit, text))
    return int(digits) if digits else None


def route_intent(
    intent: str,
    query: str,
    db: Session,
) -> Dict[str, Any]:
    """
    Route a classified intent to a concrete, read-only tool call.

    This function:
    - Never mutates state
    - Never raises
    - Always returns a safe response shape
    """

    # 🔐 Guardrail: unknown or unsupported intent
    if intent not in SUPPORTED_INTENTS:
        return {
            "answer": SAFE_FALLBACK_MESSAGE,
            "results": [],
        }

    if intent == "TRENDING_PRODUCTS":
        return {
            "answer": "Here are some trending products right now.",
            "results": get_trending_products(db),
        }

    if intent == "FILTER_PRODUCTS":
        return {
            "answer": "Here are some products that match your preferences.",
            # Pass query so tool can extract filters later
            "results": get_products_by_filters(db, query=query),
        }

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

    if intent == "SUGGEST_ALTERNATIVES":
        product_id = _extract_first_number(query)
        if product_id is None:
            return {
                "answer": "I couldn't identify which product you’re referring to.",
                "results": [],
            }

        return {
            "answer": "Here are some alternatives you might like.",
            "results": suggest_alternatives(db, product_id),
        }

    # 🔚 Defensive fallback (should never be hit)
    return {
        "answer": SAFE_FALLBACK_MESSAGE,
        "results": [],
    }
