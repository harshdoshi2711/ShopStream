# services/orders/app/domain/order_service.py

from sqlalchemy.orm import Session
import json

from services.orders.app.models.order import Order
from services.orders.app.models.product import Product
from services.orders.app.models.outbox import OutboxEvent
from common.events.order_events import OrderCreatedEvent


def create_order_with_outbox(
    *,
    db: Session,
    product_id: int,
    quantity: int,
) -> Order:
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product or product.stock < quantity:
        raise ValueError("Product unavailable")

    total_price = product.price * quantity

    order = Order(
        product_id=product_id,
        quantity=quantity,
        total_price=total_price,
        status="PENDING",
    )

    db.add(order)
    db.flush()  # ensures order.id is available

    event = OrderCreatedEvent(
        order_id=order.id,
        product_id=product_id,
        quantity=quantity,
        total_price=float(total_price),
    )

    # 🔑 SERIALIZATION BOUNDARY (THIS IS THE KEY LINE)
    payload = json.dumps({
        "order_id": event.order_id,
        "product_id": event.product_id,
        "quantity": event.quantity,
        "total_price": event.total_price,
    })

    outbox = OutboxEvent(
        event_type="OrderCreated",
        payload=payload,   # ✅ JSON STRING
    )

    db.add(outbox)
    db.commit()

    return order
