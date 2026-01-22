# scripts/seed_inventory.py

from common.database.session import SessionLocal
from services.inventory.app.models.inventory import Inventory


def seed():
    db = SessionLocal()

    db.query(Inventory).delete()

    inventory = [
        Inventory(product_id=1, stock=20),
        Inventory(product_id=2, stock=10),
        Inventory(product_id=3, stock=15),
        Inventory(product_id=4, stock=5),
        Inventory(product_id=5, stock=12),

        Inventory(product_id=6, stock=30),
        Inventory(product_id=7, stock=18),
        Inventory(product_id=8, stock=7),
        Inventory(product_id=9, stock=9),

        Inventory(product_id=10, stock=50),
        Inventory(product_id=11, stock=40),
        Inventory(product_id=12, stock=25),

        Inventory(product_id=13, stock=60),
        Inventory(product_id=14, stock=8),
        Inventory(product_id=15, stock=22),
    ]

    db.add_all(inventory)
    db.commit()
    db.close()

    print("✅ Inventory seeded successfully")


if __name__ == "__main__":
    seed()
