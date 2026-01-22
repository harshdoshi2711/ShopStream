# scripts/seed_products.py

from common.database.session import SessionLocal
from services.orders.app.models.product import Product


def seed():
    db = SessionLocal()

    db.query(Product).delete()

    products = [
        # Electronics
        Product(name="Wireless Mouse", category="electronics", price=25.99, stock=0),
        Product(name="Mechanical Keyboard", category="electronics", price=79.99, stock=0),
        Product(name="USB-C Hub", category="electronics", price=39.99, stock=0),
        Product(name="Noise Cancelling Headphones", category="electronics", price=199.99, stock=0),
        Product(name="Webcam 1080p", category="electronics", price=59.99, stock=0),

        # Lifestyle
        Product(name="Water Bottle", category="lifestyle", price=12.99, stock=0),
        Product(name="Yoga Mat", category="lifestyle", price=29.99, stock=0),
        Product(name="Desk Lamp", category="lifestyle", price=45.00, stock=0),
        Product(name="Backpack", category="lifestyle", price=69.99, stock=0),

        # Stationery
        Product(name="Notebook", category="stationery", price=3.49, stock=0),
        Product(name="Gel Pen Set", category="stationery", price=9.99, stock=0),
        Product(name="Planner", category="stationery", price=14.99, stock=0),

        # Home / Utility
        Product(name="Coffee Mug", category="home", price=8.99, stock=0),
        Product(name="Electric Kettle", category="home", price=49.99, stock=0),
        Product(name="Desk Organizer", category="home", price=19.99, stock=0),
    ]

    db.add_all(products)
    db.commit()
    db.close()

    print("✅ Products seeded successfully")


if __name__ == "__main__":
    seed()
