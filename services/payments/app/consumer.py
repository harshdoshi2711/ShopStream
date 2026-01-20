# services/payments/app/consumer.py

import json
import redis
import logging
from decimal import Decimal

from sqlalchemy.orm import Session

from common.config.logging import configure_logging
from common.database.session import SessionLocal
from common.messaging.redis_streams import publish_event
from services.orders.app.models.order import Order

configure_logging()
logger = logging.getLogger("shopstream.payments")

STREAM_NAME = "payment_events"
GROUP_NAME = "payments_group"
CONSUMER_NAME = "payments_1"


def handle_payment_attempt(payload: dict, db: Session):
    correlation_id = payload.get("correlation_id", "-")
    order_id = payload.get("order_id")
    amount_paid = payload.get("amount_paid")

    logger.info(
        "Payment attempt received",
        extra={
            "correlation_id": correlation_id,
            "order_id": order_id,
            "amount_paid": amount_paid,
        },
    )

    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        publish_event(
            "payment_results",
            {
                "type": "PaymentFailed",
                "correlation_id": correlation_id,
                "order_id": order_id,
                "amount_paid": amount_paid,
                "reason": "Order not found",
            },
        )
        return

    expected_amount = Decimal(order.total_price)
    paid_amount = Decimal(str(amount_paid))

    if paid_amount == expected_amount:
        publish_event(
            "payment_results",
            {
                "type": "PaymentSucceeded",
                "correlation_id": correlation_id,
                "order_id": order_id,
                "amount_paid": float(paid_amount),
            },
        )
        logger.info(
            "Payment successful",
            extra={
                "correlation_id": correlation_id,
                "order_id": order_id,
            },
        )
    else:
        publish_event(
            "payment_results",
            {
                "type": "PaymentFailed",
                "correlation_id": correlation_id,
                "order_id": order_id,
                "amount_paid": float(paid_amount),
                "reason": "Amount mismatch",
            },
        )
        logger.warning(
            "Payment failed",
            extra={
                "correlation_id": correlation_id,
                "order_id": order_id,
                "expected": float(expected_amount),
                "paid": float(paid_amount),
            },
        )


def run():
    redis_client = redis.Redis(
        host="redis",
        port=6379,
        decode_responses=True,
    )

    try:
        redis_client.xgroup_create(
            STREAM_NAME,
            GROUP_NAME,
            id="0",
            mkstream=True,
        )
    except redis.exceptions.ResponseError:
        pass

    logger.info(
        "Payments service started",
        extra={"correlation_id": "-"},
    )

    while True:
        messages = redis_client.xreadgroup(
            GROUP_NAME,
            CONSUMER_NAME,
            streams={STREAM_NAME: ">"},
            count=1,
            block=5000,
        )

        if not messages:
            continue

        for _, entries in messages:
            for message_id, fields in entries:
                payload = json.loads(fields["payload"])

                db = SessionLocal()
                try:
                    handle_payment_attempt(payload, db)
                    redis_client.xack(STREAM_NAME, GROUP_NAME, message_id)
                finally:
                    db.close()


if __name__ == "__main__":
    run()
