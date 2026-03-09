from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ProductSpecBase(BaseModel):
    label: str
    url: str


class ProductSpecCreate(ProductSpecBase):
    pass


class ProductSpecOut(ProductSpecBase):
    id: int
    product_id: int

    model_config = {"from_attributes": True}


class BOMItemBase(BaseModel):
    child_product_id: int
    quantity: Decimal
    unit_of_measure: str = "EA"


class BOMItemCreate(BOMItemBase):
    pass


class BOMItemOut(BOMItemBase):
    id: int
    parent_product_id: int
    child_product_name: str | None = None
    child_product_sku: str | None = None

    model_config = {"from_attributes": True}


class ProductBase(BaseModel):
    sku: str
    name: str
    description: str | None = None
    unit_price: Decimal = Decimal("0")
    unit_cost: Decimal = Decimal("0")
    unit_of_measure: str = "EA"


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    sku: str | None = None
    name: str | None = None
    description: str | None = None
    unit_price: Decimal | None = None
    unit_cost: Decimal | None = None
    unit_of_measure: str | None = None


class ProductOut(ProductBase):
    id: int
    created_at: datetime
    bom_items: list[BOMItemOut] = []
    specs: list[ProductSpecOut] = []

    model_config = {"from_attributes": True}


class CostNode(BaseModel):
    product_id: int
    sku: str
    name: str
    unit_cost: Decimal
    rolled_up_cost: Decimal
    children: list["CostNode"] = []

    model_config = {"from_attributes": True}


CostNode.model_rebuild()
