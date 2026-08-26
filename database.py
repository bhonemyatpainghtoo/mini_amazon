import sqlite3

DB_NAME = "mini_amazon.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL CHECK (stock >= 0)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart_items (
            user_id INTEGER NOT NULL,
            product_id TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK (quantity > 0),

            PRIMARY KEY (user_id, product_id),

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY (product_id)
                REFERENCES products(product_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            total REAL NOT NULL CHECK (total >= 0),
            timestamp TEXT NOT NULL,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            order_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            unit_price REAL NOT NULL CHECK (unit_price >= 0),

            PRIMARY KEY (order_id, product_id),

            FOREIGN KEY (order_id)
                REFERENCES orders(order_id)
                ON DELETE CASCADE,

            FOREIGN KEY (product_id)
                REFERENCES products(product_id)
        )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_tables()
    print("Database and tables created successfully.")