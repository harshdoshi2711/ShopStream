from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.sql import func

from common.database.session import Base


class InventoryProcessedEvent(Base):
    __tablename__ = "inventory_processed_events"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, nullable=False)
    correlation_id = Column(String, nullable=True)
    processed_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("order_id", name="uq_inventory_order_id"),
    )
