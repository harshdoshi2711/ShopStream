# services/orders/app/ui/routes.py

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from common.database.session import get_db
from services.orders.app.models.product import Product
from services.orders.app.models.order import Order

templates = Jinja2Templates(directory="services/orders/app/ui/templates")
router = APIRouter(prefix="/ui", tags=["ui"])


@router.get("/products", response_class=HTMLResponse)
def list_products(request: Request, db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return templates.TemplateResponse(
        "products.html",
        {"request": request, "products": products},
    )


@router.post("/order")
def create_order(
    product_id: int = Form(...),
    quantity: int = Form(...),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product or product.stock < quantity:
        return {"error": "Product unavailable"}

    order = Order(
        product_id=product_id,
        quantity=quantity,
        total_price=product.price * quantity,
    )

    db.add(order)
    db.commit()

    return {"status": "order created"}
