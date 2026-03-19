from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import verify_turnstile
from app.models.order import Order
from app.models.shipping import Shipment
from app.schemas.shipping import ShipmentCreate, ShipmentOut
from app.services.invoice_service import create_invoice_for_shipment

router = APIRouter(prefix="/shipments", tags=["shipping"])


@router.get("", response_model=list[ShipmentOut])
def list_shipments(db: Session = Depends(get_db)):
    return db.query(Shipment).order_by(Shipment.id.desc()).all()


@router.post("", response_model=ShipmentOut, status_code=201, dependencies=[Depends(verify_turnstile)])
def create_shipment(payload: ShipmentCreate, db: Session = Depends(get_db)):
    order = db.get(Order, payload.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    shipment = Shipment(**payload.model_dump())
    db.add(shipment)
    db.flush()

    # Auto-generate invoice
    try:
        create_invoice_for_shipment(shipment, db)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Invoice creation failed: {e}")

    db.commit()
    db.refresh(shipment)
    return shipment


@router.get("/{shipment_id}", response_model=ShipmentOut)
def get_shipment(shipment_id: int, db: Session = Depends(get_db)):
    shipment = db.get(Shipment, shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shipment
