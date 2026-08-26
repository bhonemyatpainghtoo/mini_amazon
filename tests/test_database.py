from database import get_connection


def test_database_tables_exist():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        """
    )

    tables = {row[0] for row in cursor.fetchall()}

    conn.close()

    assert "users" in tables
    assert "products" in tables
    assert "cart_items" in tables
    assert "orders" in tables
    assert "order_items" in tables