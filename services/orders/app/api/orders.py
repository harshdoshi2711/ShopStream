# services/orders/app/api/orders.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from common.database.session import get_db
from services.orders.app.domain.order_service import create_order_with_outbox

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/")
def create_order(product_id: int, quantity: int, db: Session = Depends(get_db)):
    try:
        order = create_order_with_outbox(
            db=db,
            product_id=product_id,
            quantity=quantity,
        )
    except ValueError as e:
        return {"error": str(e)}

    return {
        "order_id": order.id,
        "status": order.status,
    }
