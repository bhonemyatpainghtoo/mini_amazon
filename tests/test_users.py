from users import UserManager
from database import get_connection


def test_register_user():
    manager = UserManager()

    success, message = manager.register_user(
        "testuser",
        "password123"
    )

    assert success is True
    assert "Account created successfully" in message

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT username, password FROM users WHERE username = ?",
        ("testuser",)
    )

    user = cursor.fetchone()
    conn.close()

    assert user is not None
    assert user[0] == "testuser"
    assert user[1].startswith("$argon2")


def test_duplicate_username():
    manager = UserManager()

    manager.register_user(
        "testuser",
        "password123"
    )

    success, message = manager.register_user(
        "testuser",
        "anotherpassword"
    )

    assert success is False
    assert message == "Username already exists"


def test_login_correct_password():
    manager = UserManager()

    manager.register_user(
        "testuser",
        "password123"
    )

    success, message = manager.login_user(
        "testuser",
        "password123"
    )

    assert success is True
    assert "Welcome back" in message


def test_login_wrong_password():
    manager = UserManager()

    manager.register_user(
        "testuser",
        "password123"
    )

    success, message = manager.login_user(
        "testuser",
        "wrongpassword"
    )

    assert success is False
    assert message == "Invalid username or password"