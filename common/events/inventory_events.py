# common/events/inventory_events.py

class InventoryReservedEvent:
    def __init__(self, order_id: int, product_id: int, quantity: int):
        self.order_id = order_id
        self.product_id = product_id
        self.quantity = quantity


class InventoryFailedEvent:
    def __init__(self, order_id: int, product_id: int, reason: str):
        self.order_id = order_id
        self.product_id = product_id
        self.reason = reason
