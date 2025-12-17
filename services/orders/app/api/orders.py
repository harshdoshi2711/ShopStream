# services/orders/app/api/orders.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from common.database.session import get_db
from services.orders.app.models.product import Product
from services.orders.app.models.order import Order

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/")
def create_order(product_id: int, quantity: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product or product.stock < quantity:
        return {"error": "Product unavailable"}

    total_price = product.price * quantity

    order = Order(
        product_id=product_id,
        quantity=quantity,
        total_price=total_price,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return {"order_id": order.id, "status": order.status}
