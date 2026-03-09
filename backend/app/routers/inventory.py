from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.inventory import InventoryBalance, InventoryReservation
from app.schemas.inventory import (
    InventoryBalanceOut,
    InventoryBalanceUpsert,
    InventoryReservationOut,
)

router = APIRouter(prefix="/inventory", tags=["inventory"])


def _enrich_balance(b: InventoryBalance) -> InventoryBalanceOut:
    return InventoryBalanceOut(
        id=b.id,
        product_id=b.product_id,
        product_name=b.product.name if b.product else None,
        product_sku=b.product.sku if b.product else None,
        quantity_on_hand=b.quantity_on_hand,
    )


def _enrich_reservation(r: InventoryReservation) -> InventoryReservationOut:
    return InventoryReservationOut(
        id=r.id,
        order_id=r.order_id,
        product_id=r.product_id,
        product_name=r.product.name if r.product else None,
        quantity_reserved=r.quantity_reserved,
        created_at=r.created_at,
    )


@router.get("/balances", response_model=list[InventoryBalanceOut])
def list_balances(db: Session = Depends(get_db)):
    balances = db.query(InventoryBalance).all()
    return [_enrich_balance(b) for b in balances]


@router.post("/balances", response_model=InventoryBalanceOut, status_code=201)
def upsert_balance(payload: InventoryBalanceUpsert, db: Session = Depends(get_db)):
    balance = (
        db.query(InventoryBalance)
        .filter(InventoryBalance.product_id == payload.product_id)
        .first()
    )
    if balance:
        balance.quantity_on_hand = payload.quantity_on_hand
    else:
        balance = InventoryBalance(**payload.model_dump())
        db.add(balance)
    db.commit()
    db.refresh(balance)
    return _enrich_balance(balance)


@router.get("/reservations", response_model=list[InventoryReservationOut])
def list_reservations(order_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(InventoryReservation)
    if order_id:
        q = q.filter(InventoryReservation.order_id == order_id)
    return [_enrich_reservation(r) for r in q.all()]
