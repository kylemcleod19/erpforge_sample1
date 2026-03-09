from datetime import datetime

from pydantic import BaseModel


class ShipmentCreate(BaseModel):
    order_id: int
    shipping_account_number: str | None = None
    carrier: str | None = None
    tracking_number: str | None = None
    shipped_at: datetime | None = None
    notes: str | None = None


class ShipmentOut(BaseModel):
    id: int
    order_id: int
    shipping_account_number: str | None = None
    carrier: str | None = None
    tracking_number: str | None = None
    shipped_at: datetime | None = None
    notes: str | None = None

    model_config = {"from_attributes": True}
