# common/events/order_events.py

from dataclasses import dataclass


@dataclass
class OrderCreatedEvent:
    order_id: int
    product_id: int
    quantity: int
    total_price: float
