# services/orders/app/models/processed_event.py

from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func

from common.database.session import Base


class OrdersProcessedEvent(Base):
    __tablename__ = "orders_processed_events"

    event_id = Column(String, primary_key=True)
    processed_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
