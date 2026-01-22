# services/agent/app/tools/products.py

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from services.orders.app.models.product import Product
from services.inventory.app.models.inventory import Inventory


def get_trending_products(
    db: Session,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    Return top products based on availability and price.
    Simple heuristic for demo purposes.
    """
    products = (
        db.query(Product)
        .order_by(Product.price.desc())
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
        for p in products
    ]


def get_products_by_filters(
    db: Session,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Filter products by category and price range.
    """
    query = db.query(Product)

    if category:
        query = query.filter(Product.category == category)

    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    products = query.limit(limit).all()

    return [
        {
            "product_id": p.id,
            "name": p.name,
            "category": p.category,
            "price": float(p.price),
        }
        for p in products
    ]
