from users import UserManager
from products import ProductManager
from cart import CartManager
from orders import OrderManager
from database import get_connection


def setup_checkout_data():
    user_manager = UserManager()
    user_manager.register_user("testuser", "password123")

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


def test_create_order():
    setup_checkout_data()

    cart_manager = CartManager()
    product_manager = ProductManager()
    order_manager = OrderManager()

    cart_manager.add_to_cart(
        "testuser", "P1001", 2, product_manager
    )

    cart = cart_manager.get_cart("testuser")

    success, message, order_id = order_manager.create_order(
        "testuser",
        cart,
        product_manager,
        cart_manager
    )

    assert success is True
    assert order_id == "O0001"


def test_checkout_reduces_stock():
    setup_checkout_data()

    cart_manager = CartManager()
    product_manager = ProductManager()
    order_manager = OrderManager()

    cart_manager.add_to_cart(
        "testuser", "P1001", 2, product_manager
    )

    cart = cart_manager.get_cart("testuser")

    order_manager.create_order(
        "testuser",
        cart,
        product_manager,
        cart_manager
    )

    product = product_manager.find_product_id("P1001")

    assert product["stock"] == 48


def test_checkout_clears_cart():
    setup_checkout_data()

    cart_manager = CartManager()
    product_manager = ProductManager()
    order_manager = OrderManager()

    cart_manager.add_to_cart(
        "testuser", "P1001", 2, product_manager
    )

    cart = cart_manager.get_cart("testuser")

    order_manager.create_order(
        "testuser",
        cart,
        product_manager,
        cart_manager
    )

    assert cart_manager.get_cart("testuser") == []


def test_get_user_orders():
    setup_checkout_data()

    cart_manager = CartManager()
    product_manager = ProductManager()
    order_manager = OrderManager()

    cart_manager.add_to_cart(
        "testuser", "P1001", 2, product_manager
    )

    cart = cart_manager.get_cart("testuser")

    order_manager.create_order(
        "testuser",
        cart,
        product_manager,
        cart_manager
    )

    orders = order_manager.get_user_orders("testuser")

    assert len(orders) == 1
    assert orders[0]["order_id"] == "O0001"
    assert orders[0]["total"] == 39.98


def test_find_order_by_id():
    setup_checkout_data()

    cart_manager = CartManager()
    product_manager = ProductManager()
    order_manager = OrderManager()

    cart_manager.add_to_cart(
        "testuser", "P1001", 2, product_manager
    )

    cart = cart_manager.get_cart("testuser")

    order_manager.create_order(
        "testuser",
        cart,
        product_manager,
        cart_manager
    )

    order = order_manager.find_order_by_id("O0001")

    assert order is not None
    assert order["username"] == "testuser"
    assert order["items"][0]["product_id"] == "P1001"