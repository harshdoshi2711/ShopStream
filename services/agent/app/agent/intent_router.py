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


SAFE_FALLBACK_MESSAGE = (
    "I'm not sure how to help with that yet, "
    "but I can help you browse products, check orders, or suggest alternatives."
)


def route_intent(
    intent: str,
    query: str,
    db: Session,
) -> Dict[str, Any]:
    """
    Route classified intent to a concrete tool call.
    """

    if intent == "TRENDING_PRODUCTS":
        return {
            "answer": "Here are some trending products.",
            "results": get_trending_products(db),
        }

    if intent == "FILTER_PRODUCTS":
        return {
            "answer": "Here are some matching products.",
            "results": get_products_by_filters(db),
        }

    if intent == "ORDER_STATUS":
        try:
            order_id = int("".join(filter(str.isdigit, query)))
        except ValueError:
            return {
                "answer": "I couldn't determine the order number.",
                "results": [],
            }

        return {
            "answer": "Here is the status of your order.",
            "results": [explain_order_status(db, order_id)],
        }

    if intent == "SUGGEST_ALTERNATIVES":
        try:
            product_id = int("".join(filter(str.isdigit, query)))
        except ValueError:
            return {
                "answer": "I couldn't identify the product.",
                "results": [],
            }

        return {
            "answer": "Here are some alternatives you might like.",
            "results": suggest_alternatives(db, product_id),
        }

    # Safe, professional fallback
    return {
        "answer": SAFE_FALLBACK_MESSAGE,
        "results": [],
    }
