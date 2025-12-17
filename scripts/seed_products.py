# scripts/seed_products.py

from common.database.session import SessionLocal
from services.orders.app.models.product import Product


def seed():
    db = SessionLocal()

    db.query(Product).delete()

    products = [
        Product(name="Wireless Mouse", category="electronics", price=25.99, stock=0),
        Product(name="Mechanical Keyboard", category="electronics", price=79.99, stock=0),
        Product(name="Notebook", category="stationery", price=3.49, stock=0),
        Product(name="Water Bottle", category="lifestyle", price=12.99, stock=0),
    ]

    db.add_all(products)
    db.commit()
    db.close()

    print("Products seeded")


if __name__ == "__main__":
    seed()
