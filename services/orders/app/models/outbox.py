# services/orders/app/models/outbox.py

from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from common.database.session import Base


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id = Column(Integer, primary_key=True)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String, nullable=False, default="PENDING")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
