from products import ProductManager
from database import get_connection


def add_test_product():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO products
        (product_id, name, price, stock)
        VALUES (?, ?, ?, ?)
        """,
        ("P1001", "Wireless Mouse", 19.99, 50)
    )

    conn.commit()
    conn.close()


def test_get_products():
    add_test_product()

    manager = ProductManager()

    products = manager.get_products()

    assert len(products) == 1
    assert products[0]["product_id"] == "P1001"
    assert products[0]["name"] == "Wireless Mouse"
    assert products[0]["price"] == 19.99
    assert products[0]["stock"] == 50


def test_find_product():
    add_test_product()

    manager = ProductManager()

    product = manager.find_product_id("P1001")

    assert product is not None
    assert product["name"] == "Wireless Mouse"


def test_find_product_case_insensitive():
    add_test_product()

    manager = ProductManager()

    product = manager.find_product_id("p1001")

    assert product is not None
    assert product["product_id"] == "P1001"


def test_search_products():
    add_test_product()

    manager = ProductManager()

    products = manager.search_products("mouse")

    assert len(products) == 1
    assert products[0]["name"] == "Wireless Mouse"


def test_update_stock():
    add_test_product()

    manager = ProductManager()

    success, message = manager.update_stock(
        "P1001",
        -5
    )

    assert success is True

    product = manager.find_product_id("P1001")

    assert product["stock"] == 45


def test_cannot_reduce_stock_below_zero():
    add_test_product()

    manager = ProductManager()

    success, message = manager.update_stock(
        "P1001",
        -100
    )

    assert success is False
    assert message == "Cannot reduce stock below zero"

    product = manager.find_product_id("P1001")

    assert product["stock"] == 50