from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class PurchaseRequestStatusUpdate(BaseModel):
    status: Literal["pending", "ordered", "received"]


class PurchaseRequestOut(BaseModel):
    id: int
    order_id: int
    product_id: int
    product_name: str | None = None
    product_sku: str | None = None
    quantity_needed: Decimal
    status: str
    notes: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
