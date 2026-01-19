# services/orders/app/domain/order_service.py

import logging
import json
import uuid
from sqlalchemy.orm import Session

from services.orders.app.models.order import Order
from services.orders.app.models.product import Product
from services.orders.app.models.outbox import OutboxEvent
from common.events.order_events import OrderCreatedEvent

logger = logging.getLogger("shopstream.orders")


def create_order_with_outbox(
    *,
    db: Session,
    product_id: int,
    quantity: int,
) -> Order:
    # Correlation ID generated ONCE per order
    correlation_id = str(uuid.uuid4())

    logger.info(
        "Create order requested",
        extra={
            "correlation_id": correlation_id,
            "product_id": product_id,
            "quantity": quantity,
        },
    )

    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        logger.warning(
            "Order rejected: invalid product",
            extra={
                "correlation_id": correlation_id,
                "product_id": product_id,
            },
        )
        raise ValueError("Invalid product")

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

    # 🔑 SERIALIZATION BOUNDARY
    # Payload is JSON STRING (by design)
    payload = json.dumps({
        "correlation_id": correlation_id,
        "order_id": event.order_id,
        "product_id": event.product_id,
        "quantity": event.quantity,
        "total_price": event.total_price,
    })

    outbox = OutboxEvent(
        event_type="OrderCreated",
        payload=payload,
    )

    db.add(outbox)
    db.commit()

    logger.info(
        "Order persisted and outbox event created",
        extra={
            "correlation_id": correlation_id,
            "order_id": order.id,
            "product_id": product_id,
        },
    )

    return order
