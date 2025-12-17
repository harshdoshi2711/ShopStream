from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from common.database.session import get_db
from services.orders.app.models.product import Product
from services.orders.app.domain.order_service import create_order_with_outbox

router = APIRouter(prefix="/ui", tags=["ui"])


@router.get("/products")
def list_products(request: Request, db: Session = Depends(get_db)):
    products = db.query(Product).all()

    # Lazy import to avoid circular issues
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="services/orders/app/ui/templates")

    return templates.TemplateResponse(
        "products.html",
        {
            "request": request,
            "products": products,
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
        # Redirect back with no crash
        return RedirectResponse(
            url="/ui/products",
            status_code=303,
        )

    # Success → redirect back to products
    return RedirectResponse(
        url="/ui/products",
        status_code=303,
    )
