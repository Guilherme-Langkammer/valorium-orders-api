from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

OrderStatus = Literal[
    "pending", "confirmed", "cancelled"
]


class OrderItemCreate(BaseModel):
    product_name: str = Field(min_length=1, max_length=120)
    quantity: int = Field(gt=0)
    unit_price_cents: int = Field(ge=0)


class OrderCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=120)
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderItemRead(OrderItemCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_name: str
    status: OrderStatus
    total_cents: int
    created_at: datetime
    items: list[OrderItemRead]


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
