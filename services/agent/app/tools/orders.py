# services/agent/app/tools/orders.py

from typing import Dict, Any, List
from sqlalchemy.orm import Session

from services.orders.app.models.order import Order
from services.inventory.app.models.inventory import Inventory
from services.orders.app.models.product import Product


def explain_order_status(
    db: Session,
    order_id: int,
) -> Dict[str, Any]:
    """
    Explain why an order is in its current state.
    """
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        return {
            "order_id": order_id,
            "status": "UNKNOWN",
            "explanation": "Order does not exist.",
        }

    explanations = {
        "PENDING": "Order was created and is waiting for inventory processing.",
        "AWAITING_PAYMENT": "Inventory was reserved and payment is pending.",
        "CONFIRMED": "Payment succeeded and order is confirmed.",
        "CANCELLED": "Order was cancelled due to inventory or payment failure.",
    }

    return {
        "order_id": order.id,
        "status": order.status,
        "explanation": explanations.get(
            order.status,
            "Unknown order state.",
        ),
    }


def suggest_alternatives(
    db: Session,
    product_id: int,
    limit: int = 3,
) -> List[Dict[str, Any]]:
    """
    Suggest alternative products when an item is out of stock.
    """
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        return []

    alternatives = (
        db.query(Product)
        .filter(
            Product.category == product.category,
            Product.id != product.id,
        )
        .limit(limit)
        .all()
    )

    return [
        {
            "product_id": p.id,
            "name": p.name,
            "category": p.category,
            "price": float(p.price),
        }
        for p in alternatives
    ]
