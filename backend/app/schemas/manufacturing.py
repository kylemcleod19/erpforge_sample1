from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class WorkStationCreate(BaseModel):
    name: str
    description: str | None = None
    sequence: int = 0


class WorkStationUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    sequence: int | None = None


class WorkStationOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    sequence: int

    model_config = {"from_attributes": True}


class RoutingEntry(BaseModel):
    station_id: int
    sequence: int


class ProductRoutingOut(BaseModel):
    product_id: int
    routing: list[RoutingEntry]

    model_config = {"from_attributes": True}


class SetRoutingRequest(BaseModel):
    station_ids: list[int]  # ordered list; sequence assigned by position


class WorkOrderLogOut(BaseModel):
    id: int
    work_order_id: int
    station_id: int
    station_name: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    notes: str | None = None
    operator: str | None = None

    model_config = {"from_attributes": True}


class AdvanceWorkOrderRequest(BaseModel):
    notes: str | None = None
    operator: str | None = None


class WorkOrderOut(BaseModel):
    id: int
    order_id: int
    product_id: int
    product_name: str | None = None
    product_sku: str | None = None
    quantity: Decimal
    status: str
    current_station_sequence: int | None = None
    created_at: datetime
    bom_revision_id: int | None = None
    logs: list[WorkOrderLogOut] = []

    model_config = {"from_attributes": True}
