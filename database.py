import sqlite3
import os

# This makes sure the database file always lives right next to this
# script, no matter which folder you're standing in when you run
# python main.py. Without this, running the app from a different
# folder would quietly create a second, empty database there.
DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mini_amazon.db")


def get_connection():
    """
    Opens a connection to the SQLite database file.
    Every function in the other files calls this whenever it
    needs to read or write something — it's the one shared
    doorway into the database.
    """
    conn = sqlite3.connect(DB_NAME)

    # Without this line, SQLite won't actually enforce the
    # FOREIGN KEY rules defined below (it's off by default).
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_tables():
    """
    Creates all five tables the app needs, but only if they
    don't already exist ("IF NOT EXISTS"). Safe to call this
    every time the app starts — it won't wipe existing data.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Each registered user. AUTOINCREMENT gives every user a
    # unique numeric id automatically, and UNIQUE stops two
    # people from registering the same username.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Everything in the store. CHECK (stock >= 0) is a rule
    # enforced by the database itself — it will refuse to save
    # a product with negative stock, even if a bug in our Python
    # code tried to.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL CHECK (stock >= 0)
        )
    """)

    # What's currently sitting in each user's cart.
    # FOREIGN KEY means every row here must point at a user and
    # a product that actually exist — you can't have a cart item
    # belonging to a user_id that was never registered.
    # ON DELETE CASCADE means: if that user is ever deleted,
    # their cart rows get cleaned up automatically instead of
    # being left behind as orphaned data.
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

    # One row per completed order.
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

    # The individual line items inside each order (which
    # products, how many, at what price at the time of purchase).
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


# This block only runs if you execute this file directly
# (python database.py), not when another file imports it.
# Handy for setting up the database by hand if you ever need to.
if __name__ == "__main__":
    create_tables()
    print("Database and tables created successfully.")