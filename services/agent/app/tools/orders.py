# services/agent/app/tools/orders.py

from typing import Dict, Any, List
import logging

from sqlalchemy.orm import Session

from services.orders.app.models.order import Order
from services.inventory.app.models.inventory import Inventory
from services.orders.app.models.product import Product

logger = logging.getLogger("shopstream.shopagent.tools.orders")


def explain_order_status(
    db: Session,
    order_id: int,
) -> Dict[str, Any]:
    """
    Explain WHY an order is in its current state using saga semantics.
    """

    logger.info(
        "Explaining order outcome",
        extra={"order_id": order_id},
    )

    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        logger.warning(
            "Order not found",
            extra={"order_id": order_id},
        )
        return {
            "order_id": order_id,
            "status": "UNKNOWN",
            "explanation": "This order does not exist.",
        }

    # Base explanation
    explanation_parts: List[str] = [
        "The order was created successfully."
    ]

    # Inventory reasoning
    inventory = (
        db.query(Inventory)
        .filter(Inventory.product_id == order.product_id)
        .first()
    )

    if order.status == "PENDING":
        explanation_parts.append(
            "It is currently waiting for inventory processing."
        )

    elif order.status == "AWAITING_PAYMENT":
        explanation_parts.append(
            "Inventory was successfully reserved."
        )
        explanation_parts.append(
            "The system is waiting for payment to be completed."
        )

    elif order.status == "CONFIRMED":
        explanation_parts.append(
            "Inventory was reserved."
        )
        explanation_parts.append(
            "Payment was completed successfully."
        )
        explanation_parts.append(
            "The order is now confirmed."
        )

    elif order.status == "CANCELLED":
        # Cancellation can happen for two reasons
        if inventory and inventory.stock >= 0:
            explanation_parts.append(
                "Inventory was either unavailable or later released."
            )

        explanation_parts.append(
            "The order was cancelled because one of the required steps failed."
        )

        explanation_parts.append(
            "Any reserved inventory was released to keep the system consistent."
        )

    else:
        explanation_parts.append(
            "The order is in an unknown state."
        )

    explanation = " ".join(explanation_parts)

    logger.info(
        "Order explanation generated",
        extra={
            "order_id": order.id,
            "status": order.status,
        },
    )

    return {
        "order_id": order.id,
        "status": order.status,
        "explanation": explanation,
    }


def suggest_alternatives(
    db: Session,
    product_id: int,
    limit: int = 3,
) -> List[Dict[str, Any]]:
    """
    Suggest alternative in-stock products from the same category.
    """

    logger.info(
        "Suggesting alternatives",
        extra={"product_id": product_id},
    )

    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        logger.warning(
            "Product not found for alternatives",
            extra={"product_id": product_id},
        )
        return []

    alternatives = (
        db.query(Product, Inventory)
        .join(Inventory, Inventory.product_id == Product.id)
        .filter(
            Product.category == product.category,
            Product.id != product.id,
            Inventory.stock > 0,
        )
        .limit(limit)
        .all()
    )

    results = [
        {
            "product_id": p.id,
            "name": p.name,
            "category": p.category,
            "price": float(p.price),
            "stock": inv.stock,
        }
        for p, inv in alternatives
    ]

    logger.info(
        "Alternative suggestions ready",
        extra={
            "product_id": product_id,
            "count": len(results),
        },
    )

    return results
