# common/events/inventory_events.py

from dataclasses import dataclass


@dataclass
class InventoryReservedEvent:
    order_id: int
    product_id: int
    quantity: int


@dataclass
class InventoryFailedEvent:
    order_id: int
    product_id: int
    reason: str


@dataclass
class InventoryReleaseRequestedEvent:
    order_id: int
    product_id: int
    quantity: int
    reason: str
