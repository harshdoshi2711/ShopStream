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
    Return trending products based on available stock and price.
    More realistic than pure price ordering.
    """

    results = (
        db.query(
            Product.id,
            Product.name,
            Product.category,
            Product.price,
            Inventory.stock,
        )
        .join(Inventory, Inventory.product_id == Product.id)
        .filter(Inventory.stock > 0)
        .order_by(
            Inventory.stock.desc(),
            Product.price.desc(),
        )
        .limit(limit)
        .all()
    )

    return [
        {
            "id": r.id,
            "name": r.name,
            "category": r.category,
            "price": float(r.price),
            "stock": r.stock,
        }
        for r in results
    ]


def get_products_by_filters(
    db: Session,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Filter products by category, price range, and availability.
    """

    query = (
        db.query(
            Product.id,
            Product.name,
            Product.category,
            Product.price,
            Inventory.stock,
        )
        .join(Inventory, Inventory.product_id == Product.id)
        .filter(Inventory.stock > 0)
    )

    if category:
        query = query.filter(Product.category == category)

    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    results = query.limit(limit).all()

    return [
        {
            "id": r.id,
            "name": r.name,
            "category": r.category,
            "price": float(r.price),
            "stock": r.stock,
        }
        for r in results
    ]
