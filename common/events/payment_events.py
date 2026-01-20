# common/events/payment_events.py

from dataclasses import dataclass


@dataclass
class PaymentSucceededEvent:
    order_id: int
    amount_paid: float


@dataclass
class PaymentFailedEvent:
    order_id: int
    amount_paid: float
    reason: str
