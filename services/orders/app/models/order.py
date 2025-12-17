# services/orders/app/models/order.py

from sqlalchemy import Column, Integer, String, Numeric, DateTime
from sqlalchemy.sql import func
from common.database.session import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="PENDING")
    total_price = Column(Numeric(10, 2), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
