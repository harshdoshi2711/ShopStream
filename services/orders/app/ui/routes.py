# services/orders/app/ui/routes.py

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from common.database.session import get_db
from common.messaging.redis_streams import publish_event
from services.orders.app.models.product import Product
from services.orders.app.models.order import Order
from services.inventory.app.models.inventory import Inventory
from services.orders.app.domain.order_service import create_order_with_outbox

router = APIRouter(prefix="/ui", tags=["ui"])


@router.get("/products")
def list_products(request: Request, db: Session = Depends(get_db)):
    products = db.query(Product).order_by(Product.id).all()
    orders = db.query(Order).order_by(Order.id.desc()).all()

    # Build inventory lookup (product_id → stock)
    inventory_rows = db.query(Inventory).all()
    inventory_by_product_id = {
        row.product_id: row.stock for row in inventory_rows
    }

    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="services/orders/app/ui/templates")

    return templates.TemplateResponse(
        "products.html",
        {
            "request": request,
            "products": products,
            "orders": orders,
            "inventory": inventory_by_product_id,
        },
    )


@router.post("/order")
def create_order(
    product_id: int = Form(...),
    quantity: int = Form(...),
    db: Session = Depends(get_db),
):
    try:
        create_order_with_outbox(
            db=db,
            product_id=product_id,
            quantity=quantity,
        )
    except ValueError:
        return RedirectResponse(url="/ui/products", status_code=303)

    return RedirectResponse(url="/ui/products", status_code=303)


@router.post("/pay")
def pay_order(
    order_id: int = Form(...),
    amount_paid: float = Form(...),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return RedirectResponse(url="/ui/products", status_code=303)

    publish_event(
        "payment_events",
        {
            "type": "PaymentAttempted",
            "correlation_id": f"order-{order.id}",
            "order_id": order.id,
            "amount_paid": amount_paid,
            "expected_amount": float(order.total_price),
        },
    )

    return RedirectResponse(url="/ui/products", status_code=303)
