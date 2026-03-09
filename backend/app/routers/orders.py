from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.order import Order, OrderLineItem
from app.schemas.order import OrderLineItemOut, OrderOut, OrderStatusUpdate

router = APIRouter(prefix="/orders", tags=["orders"])

VALID_STATUSES = {"pending", "in_progress", "shipped", "invoiced", "cancelled"}


def _enrich_line_item(li: OrderLineItem) -> OrderLineItemOut:
    return OrderLineItemOut(
        id=li.id,
        order_id=li.order_id,
        product_id=li.product_id,
        product_name=li.product.name if li.product else None,
        product_sku=li.product.sku if li.product else None,
        quantity=li.quantity,
        unit_price=li.unit_price,
    )


@router.get("", response_model=list[OrderOut])
def list_orders(status: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Order)
    if status:
        q = q.filter(Order.status == status)
    return q.order_by(Order.created_at.desc()).all()


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/{order_id}/status", response_model=OrderOut)
def update_order_status(order_id: int, payload: OrderStatusUpdate, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if payload.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status: {payload.status}")
    order.status = payload.status
    db.commit()
    db.refresh(order)
    return order
