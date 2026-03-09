from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class InvoiceStatusUpdate(BaseModel):
    status: Literal["draft", "sent", "paid"]


class InvoiceLineItemOut(BaseModel):
    id: int
    invoice_id: int
    product_id: int | None = None
    description: str
    quantity: Decimal
    unit_price: Decimal
    subtotal: Decimal

    model_config = {"from_attributes": True}


class InvoiceOut(BaseModel):
    id: int
    order_id: int
    shipment_id: int
    invoice_number: str
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    created_at: datetime
    line_items: list[InvoiceLineItemOut] = []

    model_config = {"from_attributes": True}
