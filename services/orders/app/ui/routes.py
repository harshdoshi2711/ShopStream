# services/orders/app/ui/routes.py

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import requests

from common.database.session import get_db
from common.messaging.redis_streams import publish_event
from services.orders.app.models.product import Product
from services.orders.app.models.order import Order
from services.inventory.app.models.inventory import Inventory
from services.orders.app.domain.order_service import create_order_with_outbox
from services.orders.app.models.processed_event import OrdersProcessedEvent
from services.inventory.app.models.processed_event import InventoryProcessedEvent

router = APIRouter(prefix="/ui", tags=["ui"])

AGENT_URL = "http://shopagent:8001/ai/assist"


def build_saga_timeline(order_id: int, db: Session):
    """
    Build a SEMANTIC saga timeline.
    One row per business step. No retries. No duplicates.
    """

    timeline = []

    # 1️⃣ Order created
    timeline.append({
        "step": "OrderCreated",
        "source": "orders",
    })

    # Inventory events (semantic)
    inventory_events = (
        db.query(InventoryProcessedEvent)
        .filter(InventoryProcessedEvent.order_id == order_id)
        .all()
    )

    inventory_failed = False
    inventory_reserved = False
    inventory_released = False

    for evt in inventory_events:
        if evt.stream_name == "order_events":
            inventory_reserved = True
        if evt.stream_name == "inventory_release":
            inventory_released = True

    if inventory_reserved:
        timeline.append({
            "step": "InventoryReserved",
            "source": "inventory",
        })
    else:
        timeline.append({
            "step": "InventoryFailed",
            "source": "inventory",
        })

    # Payment requested (business idempotency marker)
    payment_requested = (
        db.query(OrdersProcessedEvent)
        .filter_by(
            stream_name="payment_request",
            event_id=f"payment_request:{order_id}",
        )
        .first()
        is not None
    )

    if payment_requested:
        timeline.append({
            "step": "PaymentRequested",
            "source": "orders",
        })

    # Payment outcome (from processed events)
    payment_events = (
        db.query(OrdersProcessedEvent)
        .filter(
            OrdersProcessedEvent.stream_name == "payment_events"
        )
        .all()
    )

    payment_succeeded = False
    payment_failed = False

    for evt in payment_events:
        if str(order_id) in evt.event_id:
            payment_succeeded = True

    order = db.query(Order).filter(Order.id == order_id).first()

    if order and order.status == "CONFIRMED":
        timeline.append({
            "step": "PaymentSucceeded",
            "source": "payments",
        })
    elif order and order.status == "CANCELLED":
        timeline.append({
            "step": "PaymentFailed",
            "source": "payments",
        })

    # Inventory compensation (only if payment failed)
    if inventory_released:
        timeline.append({
            "step": "InventoryReleased",
            "source": "inventory",
        })

    return timeline


@router.get("/products")
def list_products(request: Request, db: Session = Depends(get_db)):
    products = db.query(Product).order_by(Product.id).all()
    orders = db.query(Order).order_by(Order.id.desc()).all()

    inventory_rows = db.query(Inventory).all()
    inventory_by_product_id = {
        row.product_id: row.stock for row in inventory_rows
    }

    saga_timelines = {
        order.id: build_saga_timeline(order.id, db)
        for order in orders
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
            "agent_response": None,
            "saga_timelines": saga_timelines,
        },
    )


@router.post("/agent")
def ask_agent(
    request: Request,
    query: str = Form(...),
    db: Session = Depends(get_db),
):
    agent_response = {
        "answer": "ShopAgent is currently unavailable.",
        "suggestions": [],
    }

    try:
        response = requests.post(
            AGENT_URL,
            params={"query": query},
            timeout=3,
        )
        if response.ok:
            agent_response = response.json()
    except Exception:
        pass

    products = db.query(Product).order_by(Product.id).all()
    orders = db.query(Order).order_by(Order.id.desc()).all()
    inventory_rows = db.query(Inventory).all()

    inventory_by_product_id = {
        row.product_id: row.stock for row in inventory_rows
    }

    saga_timelines = {
        order.id: build_saga_timeline(order.id, db)
        for order in orders
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
            "agent_response": agent_response,
            "saga_timelines": saga_timelines,
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
        "payment_commands",
        {
            "type": "PaymentRequested",
            "correlation_id": f"order-{order.id}",
            "order_id": order.id,
            "amount_paid": amount_paid,
        },
    )

    return RedirectResponse(url="/ui/products", status_code=303)
