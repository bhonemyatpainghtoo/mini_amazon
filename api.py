from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from auth import create_access_token, decode_access_token, security
from cart import CartManager
from orders import OrderManager
from products import ProductManager
from users import UserManager
from schemas import (
    CartResponse, ErrorResponse, HealthResponse, MessageResponse,
    OrderCreatedResponse, OrderHistoryResponse, OrderResponse,
    ProductResponse, TokenResponse, UserResponse,
)


# -------------------------
# Application
# -------------------------

app = FastAPI(
    title="Mini Amazon API",
    description="REST API for the Mini Amazon e-commerce project",
    version="1.0.0",
)


# -------------------------
# Managers
# -------------------------

product_manager = ProductManager()
user_manager = UserManager()
cart_manager = CartManager()
order_manager = OrderManager()


# -------------------------
# Request Models
# -------------------------

class RegisterRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class AddCartItemRequest(BaseModel):
    product_id: str = Field(min_length=1, max_length=20)
    quantity: int = Field(gt=0, le=100)


class UpdateCartItemRequest(BaseModel):
    quantity: int = Field(gt=0, le=100)


# -------------------------
# Authentication Dependency
# -------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    username = decode_access_token(credentials.credentials)

    if not user_manager.check_username(username):
        raise HTTPException(
            status_code=401,
            detail="User no longer exists",
        )

    return username


# -------------------------
# General
# -------------------------

@app.get(
    "/",
    tags=["General"],
    summary="API root",
    response_model=MessageResponse,
)
def root():
    return {
        "message": "Mini Amazon API is running"
    }


@app.get(
    "/health",
    tags=["General"],
    summary="Health check",
    response_model=HealthResponse,
)
def health_check():
    return {
        "status": "healthy"
    }


# -------------------------
# Authentication
# -------------------------

@app.post(
    "/auth/register",
    tags=["Authentication"],
    summary="Register a new user",
    status_code=201,
    response_model=MessageResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid registration details"},
        409: {"model": ErrorResponse, "description": "Username already exists"},
    },
)
def register_user(data: RegisterRequest):
    success, message = user_manager.register_user(
        data.username,
        data.password,
    )

    if not success:
        if message == "Username already exists":
            raise HTTPException(
                status_code=409,
                detail=message,
            )

        raise HTTPException(
            status_code=400,
            detail=message,
        )

    return {
        "message": message
    }


@app.post(
    "/auth/login",
    tags=["Authentication"],
    summary="Login user",
    response_model=TokenResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid username or password"},
    },
)
def login_user(data: LoginRequest):
    success, _ = user_manager.login_user(
        data.username,
        data.password,
    )

    if not success:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    access_token = create_access_token(
        data.username.lower().strip()
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@app.get(
    "/auth/me",
    tags=["Authentication"],
    summary="Get current authenticated user",
    response_model=UserResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or expired authentication token"},
        403: {"model": ErrorResponse, "description": "Bearer credentials required"},
    },
)
def get_me(
    username: str = Depends(get_current_user),
):
    return {
        "username": username
    }


# -------------------------
# Products
# -------------------------

@app.get(
    "/products",
    tags=["Products"],
    summary="List all products",
    response_model=list[ProductResponse],
)
def get_products():
    return product_manager.get_products()


@app.get(
    "/products/search",
    tags=["Products"],
    summary="Search products",
    response_model=list[ProductResponse],
    responses={
        404: {"model": ErrorResponse, "description": "No products found"},
    },
)
def search_products(keyword: str):
    products = product_manager.search_products(keyword)

    if not products:
        raise HTTPException(
            status_code=404,
            detail="No products found",
        )

    return products


@app.get(
    "/products/{product_id}",
    tags=["Products"],
    summary="Get product by ID",
    response_model=ProductResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Product not found"},
    },
)
def get_product(product_id: str):
    product = product_manager.find_product_id(product_id)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return product


# -------------------------
# Cart
# -------------------------

@app.get(
    "/cart",
    tags=["Cart"],
    summary="Get current user's cart",
    response_model=CartResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or expired authentication token"},
        403: {"model": ErrorResponse, "description": "Bearer credentials required"},
    },
)
def get_cart(
    username: str = Depends(get_current_user),
):
    cart = cart_manager.get_cart(username)

    return {
        "username": username,
        "items": cart,
    }


@app.post(
    "/cart/items",
    tags=["Cart"],
    summary="Add item to current user's cart",
    status_code=201,
    response_model=MessageResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Cart item could not be added"},
        401: {"model": ErrorResponse, "description": "Invalid or expired authentication token"},
        403: {"model": ErrorResponse, "description": "Bearer credentials required"},
    },
)
def add_cart_item(
    data: AddCartItemRequest,
    username: str = Depends(get_current_user),
):
    success, message = cart_manager.add_to_cart(
        username,
        data.product_id,
        data.quantity,
        product_manager,
    )

    if not success:
        raise HTTPException(
            status_code=400,
            detail=message,
        )

    return {
        "message": message
    }


@app.patch(
    "/cart/items/{product_id}",
    tags=["Cart"],
    summary="Update cart item quantity",
    response_model=MessageResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Cart quantity could not be updated"},
        401: {"model": ErrorResponse, "description": "Invalid or expired authentication token"},
        403: {"model": ErrorResponse, "description": "Bearer credentials required"},
    },
)
def update_cart_item(
    product_id: str,
    data: UpdateCartItemRequest,
    username: str = Depends(get_current_user),
):
    success, message = cart_manager.update_quantity(
        username,
        product_id,
        data.quantity,
        product_manager,
    )

    if not success:
        raise HTTPException(
            status_code=400,
            detail=message,
        )

    return {
        "message": message
    }


@app.delete(
    "/cart/items/{product_id}",
    tags=["Cart"],
    summary="Remove item from current user's cart",
    response_model=MessageResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or expired authentication token"},
        403: {"model": ErrorResponse, "description": "Bearer credentials required"},
        404: {"model": ErrorResponse, "description": "Cart item not found"},
    },
)
def remove_cart_item(
    product_id: str,
    username: str = Depends(get_current_user),
):
    success, message = cart_manager.remove_from_cart(
        username,
        product_id,
    )

    if not success:
        raise HTTPException(
            status_code=404,
            detail=message,
        )

    return {
        "message": message
    }


@app.delete(
    "/cart",
    tags=["Cart"],
    summary="Clear current user's cart",
    response_model=MessageResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Cart could not be cleared"},
        401: {"model": ErrorResponse, "description": "Invalid or expired authentication token"},
        403: {"model": ErrorResponse, "description": "Bearer credentials required"},
    },
)
def clear_cart(
    username: str = Depends(get_current_user),
):
    success, message = cart_manager.clear_cart(username)

    if not success:
        raise HTTPException(
            status_code=400,
            detail=message,
        )

    return {
        "message": message
    }

# -------------------------
# Orders
# -------------------------

@app.post(
    "/orders",
    tags=["Orders"],
    summary="Checkout the current user's cart",
    status_code=201,
    response_model=OrderCreatedResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Checkout failed, for example an empty cart or insufficient stock"},
        401: {"model": ErrorResponse, "description": "Invalid or expired authentication token"},
        403: {"model": ErrorResponse, "description": "Bearer credentials required"},
    },
)
def create_order(username: str = Depends(get_current_user)):
    # OrderManager reads the cart and checks stock inside one transaction.
    success, message, order_id = order_manager.create_order(
        username, None, product_manager, cart_manager,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {"message": message, "order_id": order_id}


@app.get(
    "/orders",
    tags=["Orders"],
    summary="Get current user's order history",
    response_model=OrderHistoryResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or expired authentication token"},
        403: {"model": ErrorResponse, "description": "Bearer credentials required"},
    },
)
def get_orders(username: str = Depends(get_current_user)):
    return {
        "username": username,
        "orders": order_manager.get_user_orders(username),
    }


@app.get(
    "/orders/{order_id}",
    tags=["Orders"],
    summary="Get an order belonging to the current user",
    response_model=OrderResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or expired authentication token"},
        403: {"model": ErrorResponse, "description": "Bearer credentials required"},
        404: {"model": ErrorResponse, "description": "Order not found"},
    },
)
def get_order(order_id: str, username: str = Depends(get_current_user)):
    order = order_manager.find_order_by_id(order_id)

    # Use the same response for a missing order and another user's order.
    if order is None or order["username"] != username:
        raise HTTPException(status_code=404, detail="Order not found")

    return order
