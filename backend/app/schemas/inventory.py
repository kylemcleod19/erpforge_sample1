from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class InventoryBalanceUpsert(BaseModel):
    product_id: int
    quantity_on_hand: Decimal


class InventoryBalanceOut(BaseModel):
    id: int
    product_id: int
    product_name: str | None = None
    product_sku: str | None = None
    quantity_on_hand: Decimal

    model_config = {"from_attributes": True}


class InventoryReservationOut(BaseModel):
    id: int
    order_id: int
    product_id: int
    product_name: str | None = None
    quantity_reserved: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}
