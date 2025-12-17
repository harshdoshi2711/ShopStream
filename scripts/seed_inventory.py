# scripts/seed_inventory.py

from common.database.session import SessionLocal
from services.inventory.app.models.inventory import Inventory


def seed():
    db = SessionLocal()

    db.query(Inventory).delete()

    inventory = [
        Inventory(product_id=1, stock=10),
        Inventory(product_id=2, stock=5),
        Inventory(product_id=3, stock=0),
        Inventory(product_id=4, stock=20),
    ]

    db.add_all(inventory)
    db.commit()
    db.close()

    print("Inventory seeded")


if __name__ == "__main__":
    seed()
