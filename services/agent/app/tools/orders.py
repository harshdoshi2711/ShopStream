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
    Explain why an order is in its current state.
    """

    logger.info(
        "Explaining order status",
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
            "explanation": "Order does not exist.",
        }

    explanations = {
        "PENDING": "Your order was created and is waiting for inventory processing.",
        "AWAITING_PAYMENT": "Inventory was reserved and payment is pending.",
        "CONFIRMED": "Payment succeeded and your order is confirmed.",
        "CANCELLED": "The order was cancelled due to inventory or payment failure.",
    }

    explanation = explanations.get(
        order.status,
        "The order is in an unknown state.",
    )

    logger.info(
        "Order status resolved",
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
