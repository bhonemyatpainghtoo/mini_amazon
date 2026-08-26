from users import UserManager
from products import ProductManager
from cart import CartManager
from database import get_connection


def setup_user_and_product():
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


def test_add_to_cart():
    setup_user_and_product()

    cart_manager = CartManager()
    product_manager = ProductManager()

    success, message = cart_manager.add_to_cart(
        "testuser",
        "P1001",
        2,
        product_manager
    )

    assert success is True

    cart = cart_manager.get_cart("testuser")

    assert len(cart) == 1
    assert cart[0]["product_id"] == "P1001"
    assert cart[0]["quantity"] == 2


def test_add_same_product_increases_quantity():
    setup_user_and_product()

    cart_manager = CartManager()
    product_manager = ProductManager()

    cart_manager.add_to_cart(
        "testuser", "P1001", 2, product_manager
    )

    cart_manager.add_to_cart(
        "testuser", "P1001", 3, product_manager
    )

    cart = cart_manager.get_cart("testuser")

    assert len(cart) == 1
    assert cart[0]["quantity"] == 5


def test_cannot_add_more_than_stock():
    setup_user_and_product()

    cart_manager = CartManager()
    product_manager = ProductManager()

    success, message = cart_manager.add_to_cart(
        "testuser",
        "P1001",
        100,
        product_manager
    )

    assert success is False
    assert cart_manager.get_cart("testuser") == []


def test_update_quantity():
    setup_user_and_product()

    cart_manager = CartManager()
    product_manager = ProductManager()

    cart_manager.add_to_cart(
        "testuser", "P1001", 2, product_manager
    )

    success, message = cart_manager.update_quantity(
        "testuser",
        "P1001",
        5,
        product_manager
    )

    assert success is True

    cart = cart_manager.get_cart("testuser")

    assert cart[0]["quantity"] == 5


def test_remove_from_cart():
    setup_user_and_product()

    cart_manager = CartManager()
    product_manager = ProductManager()

    cart_manager.add_to_cart(
        "testuser", "P1001", 2, product_manager
    )

    success, message = cart_manager.remove_from_cart(
        "testuser",
        "P1001"
    )

    assert success is True
    assert cart_manager.get_cart("testuser") == []


def test_clear_cart():
    setup_user_and_product()

    cart_manager = CartManager()
    product_manager = ProductManager()

    cart_manager.add_to_cart(
        "testuser", "P1001", 2, product_manager
    )

    success, message = cart_manager.clear_cart("testuser")

    assert success is True
    assert cart_manager.get_cart("testuser") == []


def test_calculate_total():
    setup_user_and_product()

    cart_manager = CartManager()
    product_manager = ProductManager()

    cart_manager.add_to_cart(
        "testuser", "P1001", 3, product_manager
    )

    total = cart_manager.calculate_total(
        "testuser",
        product_manager
    )

    assert total == 59.97