# services/inventory/app/models/inventory.py

from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func

from common.database.session import Base


class Inventory(Base):
    __tablename__ = "inventory"

    product_id = Column(Integer, primary_key=True)
    stock = Column(Integer, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
