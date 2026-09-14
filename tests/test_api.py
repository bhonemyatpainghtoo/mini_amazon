"""Exercise real HTTP routes, authentication and SQLite transactions."""

import importlib
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

from database import get_connection


@pytest.fixture
def client(test_database, monkeypatch):
    # Configure before importing the API; never depend on a developer's .env.
    monkeypatch.setenv("JWT_SECRET", "test-only-secret-that-is-at-least-32-bytes-long")
    auth = importlib.import_module("auth")
    monkeypatch.setattr(auth, "SECRET_KEY", "test-only-secret-that-is-at-least-32-bytes-long")
    api = importlib.import_module("api")
    with TestClient(api.app) as test_client:
        yield test_client


@pytest.fixture
def products(test_database):
    conn = get_connection()
    try:
        conn.executemany(
            "INSERT INTO products (product_id, name, price, stock) VALUES (?, ?, ?, ?)",
            [("P1001", "Mouse", 19.99, 5), ("P1002", "Keyboard", 30.0, 3)],
        )
        conn.commit()
    finally:
        conn.close()


def login(client, username):
    credentials = {"username": username, "password": "password123"}
    assert client.post("/auth/register", json=credentials).status_code == 201
    response = client.post("/auth/login", json=credentials)
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def add_item(client, headers, product_id="P1001", quantity=2):
    response = client.post(
        "/cart/items", headers=headers,
        json={"product_id": product_id, "quantity": quantity},
    )
    assert response.status_code == 201


def test_checkout_and_history(client, products):
    headers = login(client, "Alice")
    add_item(client, headers)
    add_item(client, headers, "P1002", 1)
    response = client.post("/orders", headers=headers)
    assert response.status_code == 201
    order_id = response.json()["order_id"]
    order = client.get(f"/orders/{order_id}", headers=headers).json()
    assert order["username"] == "alice"
    assert order["total"] == pytest.approx(69.98)
    assert {i["product_id"]: i["quantity"] for i in order["items"]} == {
        "P1001": 2, "P1002": 1,
    }
    assert client.get("/orders", headers=headers).json()["orders"] == [order]
    assert client.get("/cart", headers=headers).json()["items"] == []
    assert client.get("/products/P1001").json()["stock"] == 3
    assert client.get("/products/P1002").json()["stock"] == 2
    # Repeating checkout must not create another order or reduce stock again.
    assert client.post("/orders", headers=headers).status_code == 400
    assert client.get("/orders", headers=headers).json()["orders"] == [order]
    assert client.get("/products/P1001").json()["stock"] == 3


def test_orders_are_private(client, products):
    alice = login(client, "alice")
    bob = login(client, "bob")
    add_item(client, alice)
    add_item(client, bob, quantity=1)
    created = client.post("/orders?username=bob", headers=alice)
    assert created.status_code == 201
    order_id = created.json()["order_id"]
    missing = client.get("/orders/O9999", headers=bob)
    forbidden = client.get(f"/orders/{order_id}", headers=bob)
    assert missing.status_code == forbidden.status_code == 404
    assert missing.json() == forbidden.json() == {"detail": "Order not found"}
    assert client.get("/orders", headers=bob).json()["orders"] == []
    assert client.get("/cart", headers=bob).json()["items"] == [
        {"product_id": "P1001", "quantity": 1},
    ]


@pytest.mark.parametrize("method,path", [
    ("POST", "/orders"), ("GET", "/orders"), ("GET", "/orders/O0001"),
])
@pytest.mark.parametrize("token_kind", ["missing", "malformed", "expired", "wrong_signature"])
def test_order_routes_require_valid_authentication(client, method, path, token_kind):
    auth = importlib.import_module("auth")
    claims = {"sub": "alice", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}
    headers = {}
    if token_kind == "malformed":
        headers["Authorization"] = "Bearer invalid"
    elif token_kind in ("expired", "wrong_signature"):
        key = auth.SECRET_KEY
        if token_kind == "expired":
            claims["exp"] = datetime.now(timezone.utc) - timedelta(minutes=5)
        else:
            key = "different-test-secret-at-least-32-bytes-long"
        headers["Authorization"] = f"Bearer {jwt.encode(claims, key, algorithm=auth.ALGORITHM)}"
    response = client.request(method, path, headers=headers)
    # FastAPI 0.115.6 returns 403 for absent bearer credentials.
    assert response.status_code == (403 if token_kind == "missing" else 401)


def test_checkout_empty_cart(client):
    headers = login(client, "alice")
    response = client.post("/orders", headers=headers)
    assert response.status_code == 400
    assert response.json() == {"detail": "Your cart is empty"}
    assert client.get("/orders", headers=headers).json()["orders"] == []


def test_insufficient_stock_preserves_cart_and_inventory(client, products):
    headers = login(client, "alice")
    add_item(client, headers)
    add_item(client, headers, "P1002", 2)
    conn = get_connection()
    try:
        conn.execute("UPDATE products SET stock = 1 WHERE product_id = 'P1002'")
        conn.commit()
    finally:
        conn.close()
    before = client.get("/cart", headers=headers).json()
    response = client.post("/orders", headers=headers)
    assert response.status_code == 400
    assert "Not enough stock" in response.json()["detail"]
    assert client.get("/cart", headers=headers).json() == before
    assert client.get("/orders", headers=headers).json()["orders"] == []
    assert client.get("/products/P1001").json()["stock"] == 5
    assert client.get("/products/P1002").json()["stock"] == 1


def test_database_failure_rolls_back_checkout(client, products):
    headers = login(client, "alice")
    add_item(client, headers)
    conn = get_connection()
    try:
        # Fail at the last step, after order insertion and stock reduction.
        conn.execute("""
            CREATE TRIGGER fail_cart_clear BEFORE DELETE ON cart_items
            BEGIN SELECT RAISE(ABORT, 'simulated checkout failure'); END
        """)
        conn.commit()
    finally:
        conn.close()
    before = client.get("/cart", headers=headers).json()
    assert client.post("/orders", headers=headers).status_code == 400
    assert client.get("/cart", headers=headers).json() == before
    assert client.get("/orders", headers=headers).json()["orders"] == []
    assert client.get("/products/P1001").json()["stock"] == 5
    conn = get_connection()
    try:
        assert conn.execute("SELECT COUNT(*) FROM order_items").fetchone()[0] == 0
    finally:
        conn.close()


def test_deleted_user_token_is_rejected(client):
    headers = login(client, "alice")
    conn = get_connection()
    try:
        conn.execute("DELETE FROM users WHERE username = 'alice'")
        conn.commit()
    finally:
        conn.close()
    assert client.get("/orders", headers=headers).status_code == 401


def test_swagger_describes_nested_orders_and_errors(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    schemas = spec["components"]["schemas"]
    checkout = spec["paths"]["/orders"]["post"]["responses"]
    assert checkout["201"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "/OrderCreatedResponse"
    )
    assert checkout["400"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "/ErrorResponse"
    )
    assert schemas["OrderResponse"]["properties"]["items"]["items"]["$ref"].endswith(
        "/OrderItemResponse"
    )
    assert schemas["OrderItemResponse"]["properties"]["unit_price"]["type"] == "number"
    assert schemas["OrderCreatedResponse"]["properties"]["order_id"]["examples"] == ["O0001"]


def test_response_models_preserve_public_and_cart_routes(client, products):
    assert client.get("/").json() == {"message": "Mini Amazon API is running"}
    assert client.get("/health").json() == {"status": "healthy"}
    catalog = client.get("/products")
    assert catalog.status_code == 200
    assert len(catalog.json()) == 2
    assert client.get("/products/search", params={"keyword": "Mouse"}).json() == [
        {"product_id": "P1001", "name": "Mouse", "price": 19.99, "stock": 5},
    ]
    headers = login(client, "alice")
    assert client.get("/auth/me", headers=headers).json() == {"username": "alice"}
    add_item(client, headers)
    updated = client.patch("/cart/items/P1001", headers=headers, json={"quantity": 3})
    assert updated.status_code == 200
    assert isinstance(updated.json()["message"], str)
    assert client.get("/cart", headers=headers).json() == {
        "username": "alice", "items": [{"product_id": "P1001", "quantity": 3}],
    }
    assert client.delete("/cart/items/P1001", headers=headers).status_code == 200
    add_item(client, headers)
    cleared = client.delete("/cart", headers=headers)
    assert cleared.status_code == 200
    assert isinstance(cleared.json()["message"], str)
    assert client.get("/cart", headers=headers).json()["items"] == []


def test_response_validation_rejects_broken_product_data(client, monkeypatch):
    from fastapi.exceptions import ResponseValidationError

    api = importlib.import_module("api")
    monkeypatch.setattr(
        api.product_manager, "get_products",
        lambda: [{"product_id": "P1001", "name": "Mouse", "price": "not-a-price", "stock": 5}],
    )
    with pytest.raises(ResponseValidationError):
        client.get("/products")
