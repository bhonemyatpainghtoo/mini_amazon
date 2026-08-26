import json
from database import get_connection


def migrate_products():
    with open("products.json", "r") as file:
        products = json.load(file)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        for product in products:
            cursor.execute(
                """
                INSERT OR IGNORE INTO products
                (product_id, name, price, stock)
                VALUES (?, ?, ?, ?)
                """,
                (
                    product["product_id"],
                    product["name"],
                    product["price"],
                    product["stock"]
                )
            )

        conn.commit()
        print(f"Migrated {len(products)} products successfully.")

    finally:
        conn.close()


if __name__ == "__main__":
    migrate_products()