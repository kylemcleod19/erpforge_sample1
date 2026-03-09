from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class QuoteLineItemCreate(BaseModel):
    product_id: int
    quantity: Decimal
    unit_price: Decimal
    lead_time_days: int | None = None


class QuoteLineItemOut(BaseModel):
    id: int
    quote_id: int
    product_id: int
    product_name: str | None = None
    product_sku: str | None = None
    quantity: Decimal
    unit_price: Decimal
    lead_time_days: int | None = None
    subtotal: Decimal

    model_config = {"from_attributes": True}


class QuoteCreate(BaseModel):
    customer_name: str
    customer_email: str | None = None
    expires_at: datetime | None = None
    notes: str | None = None


class QuoteUpdate(BaseModel):
    customer_name: str | None = None
    customer_email: str | None = None
    expires_at: datetime | None = None
    notes: str | None = None


class QuoteStatusTransition(BaseModel):
    status: Literal["review", "approved", "sent", "won", "lost"]


class QuoteOut(BaseModel):
    id: int
    customer_name: str
    customer_email: str | None = None
    status: str
    expires_at: datetime | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    line_items: list[QuoteLineItemOut] = []

    model_config = {"from_attributes": True}
