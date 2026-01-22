# services/payments/app/consumer.py

import json
import redis
import logging
from decimal import Decimal

from sqlalchemy.orm import Session

from common.config.logging import configure_logging
from common.database.session import SessionLocal
from common.messaging.redis_streams import publish_event
from common.messaging.dead_letter import send_to_dlq

from services.orders.app.models.order import Order

configure_logging()
logger = logging.getLogger("shopstream.payments")

PAYMENT_COMMANDS_STREAM = "payment_commands"
PAYMENT_EVENTS_STREAM = "payment_events"

GROUP_NAME = "payments_group"
CONSUMER_NAME = "payments_1"


def handle_payment_request(payload: dict, db: Session):
    correlation_id = payload.get("correlation_id", "-")
    order_id = payload["order_id"]
    amount_paid = Decimal(str(payload.get("amount_paid", 0)))

    logger.info(
        "Payment attempt received",
        extra={
            "correlation_id": correlation_id,
            "order_id": order_id,
            "amount_paid": float(amount_paid),
        },
    )

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        logger.warning(
            "Payment failed: order not found",
            extra={"correlation_id": correlation_id, "order_id": order_id},
        )

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

    if order.status != "AWAITING_PAYMENT":
        logger.info(
            "Ignoring payment attempt for non-payable order",
            extra={
                "correlation_id": correlation_id,
                "order_id": order_id,
                "status": order.status,
            },
        )
        return

    expected = Decimal(order.total_price)

    if amount_paid == expected:
        logger.info(
            "Payment successful",
            extra={"correlation_id": correlation_id, "order_id": order_id},
        )

        publish_event(
            PAYMENT_EVENTS_STREAM,
            {
                "type": "PaymentSucceeded",
                "correlation_id": correlation_id,
                "order_id": order_id,
                "amount_paid": float(amount_paid),
            },
        )
    else:
        logger.warning(
            "Payment failed: incorrect amount",
            extra={
                "correlation_id": correlation_id,
                "order_id": order_id,
                "expected": float(expected),
                "paid": float(amount_paid),
            },
        )

        publish_event(
            PAYMENT_EVENTS_STREAM,
            {
                "type": "PaymentFailed",
                "correlation_id": correlation_id,
                "order_id": order_id,
                "amount_paid": float(amount_paid),
                "reason": "Incorrect amount",
            },
        )


def run():
    redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

    try:
        redis_client.xgroup_create(
            PAYMENT_COMMANDS_STREAM, GROUP_NAME, id="0", mkstream=True
        )
    except redis.exceptions.ResponseError:
        pass

    logger.info("Payments consumer started", extra={"correlation_id": "-"})

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
                        PAYMENT_COMMANDS_STREAM, GROUP_NAME, message_id
                    )

                except Exception as e:
                    db.rollback()

                    logger.exception(
                        "Unhandled error in payments consumer",
                        extra={
                            "correlation_id": payload.get("correlation_id", "-"),
                            "event_id": message_id,
                        },
                    )

                    send_to_dlq(
                        source_stream=PAYMENT_COMMANDS_STREAM,
                        message_id=message_id,
                        payload=payload,
                        error=e,
                    )

                    redis_client.xack(
                        PAYMENT_COMMANDS_STREAM, GROUP_NAME, message_id
                    )

                finally:
                    db.close()


if __name__ == "__main__":
    run()
