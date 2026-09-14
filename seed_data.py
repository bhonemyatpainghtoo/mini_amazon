"""
Seeds the database with demo products so the app is usable
right after a fresh clone. Safe to run multiple times — it
only inserts products that don't already exist.
"""

from database import get_connection, create_tables

DEMO_PRODUCTS = [
    ("P1001", "Wireless Mouse", 19.99, 50),
    ("P1002", "Mechanical Keyboard", 64.99, 30),
    ("P1003", "USB-C Hub", 24.50, 40),
    ("P1004", "27in Monitor", 189.00, 15),
    ("P1005", "Webcam 1080p", 39.99, 25),
    ("P1006", "Noise Cancelling Headphones", 89.99, 20),
]


def seed_products():
    create_tables()

    conn = get_connection()
    cursor = conn.cursor()

    inserted = 0

    try:
        for product_id, name, price, stock in DEMO_PRODUCTS:
            cursor.execute(
                """
                INSERT OR IGNORE INTO products
                (product_id, name, price, stock)
                VALUES (?, ?, ?, ?)
                """,
                (product_id, name, price, stock)
            )
            if cursor.rowcount:
                inserted += 1

        conn.commit()
        return inserted

    finally:
        conn.close()


if __name__ == "__main__":
    count = seed_products()
    print(f"Seeded {count} new product(s). Database ready to go.")