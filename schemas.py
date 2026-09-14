"""Public response shapes used for validation and Swagger documentation."""

from typing import Literal

from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    message: str = Field(examples=["Item added to cart"])


class HealthResponse(BaseModel):
    status: Literal["healthy"]


class TokenResponse(BaseModel):
    access_token: str = Field(description="Signed JWT returned after login.")
    token_type: Literal["bearer"]


class UserResponse(BaseModel):
    username: str = Field(examples=["checkout_test"])


class ProductResponse(BaseModel):
    product_id: str = Field(examples=["P1001"])
    name: str = Field(examples=["Wireless Mouse"])
    price: float = Field(examples=[19.99])
    stock: int = Field(examples=[50])


class CartItemResponse(BaseModel):
    product_id: str = Field(examples=["P1001"])
    quantity: int = Field(examples=[2])


class CartResponse(UserResponse):
    items: list[CartItemResponse]


class OrderItemResponse(CartItemResponse):
    unit_price: float = Field(examples=[19.99])


class OrderResponse(UserResponse):
    order_id: str = Field(examples=["O0001"])
    total: float = Field(examples=[39.98])
    # Keep the current database string format in the public response.
    timestamp: str = Field(examples=["2026-09-15 12:00:00"])
    items: list[OrderItemResponse]


class OrderHistoryResponse(UserResponse):
    orders: list[OrderResponse]


class OrderCreatedResponse(MessageResponse):
    message: str = Field(examples=["Order placed successfully!"])
    order_id: str = Field(examples=["O0001"])


class ErrorResponse(BaseModel):
    detail: str = Field(examples=["Your cart is empty"])
