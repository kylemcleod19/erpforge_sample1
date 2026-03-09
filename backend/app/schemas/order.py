from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class OrderLineItemOut(BaseModel):
    id: int
    order_id: int
    product_id: int
    product_name: str | None = None
    product_sku: str | None = None
    quantity: Decimal
    unit_price: Decimal

    model_config = {"from_attributes": True}


class OrderStatusUpdate(BaseModel):
    status: str


class OrderOut(BaseModel):
    id: int
    quote_id: int | None = None
    status: str
    notes: str | None = None
    created_at: datetime
    line_items: list[OrderLineItemOut] = []

    model_config = {"from_attributes": True}
