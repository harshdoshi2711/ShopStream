# services/payments/app/consumer.py

import json
import redis
import logging
import random
from decimal import Decimal

from sqlalchemy.orm import Session

from common.config.logging import configure_logging
from common.database.session import SessionLocal
from common.messaging.redis_streams import publish_event
from services.orders.app.models.order import Order

configure_logging()
logger = logging.getLogger("shopstream.payments")

PAYMENT_COMMANDS_STREAM = "payment_commands"
PAYMENT_EVENTS_STREAM = "payment_events"

GROUP_NAME = "payments_group"
CONSUMER_NAME = "payments_1"


def handle_payment_request(payload: dict, db: Session):
    correlation_id = payload.get("correlation_id", "-")
    order_id = payload.get("order_id")
    amount_due = Decimal(str(payload.get("amount_due", 0)))

    logger.info(
        "Payment request received",
        extra={
            "correlation_id": correlation_id,
            "order_id": order_id,
            "amount_due": float(amount_due),
        },
    )

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        publish_event(
            PAYMENT_EVENTS_STREAM,
            {
                "type": "PaymentFailed",
                "correlation_id": correlation_id,
                "order_id": order_id,
                "reason": "Order not found",
            },
        )
        return

    # 🛑 Terminal guard
    if order.status in ("CONFIRMED", "CANCELLED"):
        return

    # 🧪 Simulate payment outcome (for now)
    payment_successful = random.choice([True, False])

    if payment_successful:
        publish_event(
            PAYMENT_EVENTS_STREAM,
            {
                "type": "PaymentSucceeded",
                "correlation_id": correlation_id,
                "order_id": order_id,
                "amount_paid": float(amount_due),
            },
        )

        logger.info(
            "Payment succeeded",
            extra={
                "correlation_id": correlation_id,
                "order_id": order_id,
            },
        )
    else:
        publish_event(
            PAYMENT_EVENTS_STREAM,
            {
                "type": "PaymentFailed",
                "correlation_id": correlation_id,
                "order_id": order_id,
                "reason": "Payment declined",
            },
        )

        logger.warning(
            "Payment failed",
            extra={
                "correlation_id": correlation_id,
                "order_id": order_id,
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
            PAYMENT_COMMANDS_STREAM,
            GROUP_NAME,
            id="0",
            mkstream=True,
        )
    except redis.exceptions.ResponseError:
        pass

    logger.info("Payments service started", extra={"correlation_id": "-"})

    while True:
        messages = redis_client.xreadgroup(
            GROUP_NAME,
            CONSUMER_NAME,
            streams={PAYMENT_COMMANDS_STREAM: ">"},
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
                    handle_payment_request(payload, db)
                    redis_client.xack(
                        PAYMENT_COMMANDS_STREAM,
                        GROUP_NAME,
                        message_id,
                    )
                finally:
                    db.close()


if __name__ == "__main__":
    run()
