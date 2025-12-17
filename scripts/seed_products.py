# scripts/seed_products.py

from common.database.session import SessionLocal
from services.orders.app.models.product import Product


def seed():
    db = SessionLocal()

    if db.query(Product).count() > 0:
        print("Products already seeded")
        return

    products = [
        Product(name="Wireless Mouse", category="electronics", price=25.99, stock=100),
        Product(name="Mechanical Keyboard", category="electronics", price=79.99, stock=50),
        Product(name="Notebook", category="stationery", price=3.49, stock=500),
        Product(name="Water Bottle", category="lifestyle", price=12.99, stock=200),
    ]

    db.add_all(products)
    db.commit()
    db.close()

    print("Seeded products successfully")


if __name__ == "__main__":
    seed()
