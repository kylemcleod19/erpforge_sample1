from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.purchasing import PurchaseRequest
from app.schemas.purchasing import PurchaseRequestOut, PurchaseRequestStatusUpdate

router = APIRouter(prefix="/purchasing", tags=["purchasing"])


def _enrich(pr: PurchaseRequest) -> PurchaseRequestOut:
    return PurchaseRequestOut(
        id=pr.id,
        order_id=pr.order_id,
        product_id=pr.product_id,
        product_name=pr.product.name if pr.product else None,
        product_sku=pr.product.sku if pr.product else None,
        quantity_needed=pr.quantity_needed,
        status=pr.status,
        notes=pr.notes,
        created_at=pr.created_at,
    )


@router.get("/requests", response_model=list[PurchaseRequestOut])
def list_purchase_requests(status: str | None = None, db: Session = Depends(get_db)):
    q = db.query(PurchaseRequest)
    if status:
        q = q.filter(PurchaseRequest.status == status)
    return [_enrich(pr) for pr in q.order_by(PurchaseRequest.created_at.desc()).all()]


@router.patch("/requests/{request_id}/status", response_model=PurchaseRequestOut)
def update_purchase_request_status(
    request_id: int,
    payload: PurchaseRequestStatusUpdate,
    db: Session = Depends(get_db),
):
    pr = db.get(PurchaseRequest, request_id)
    if not pr:
        raise HTTPException(status_code=404, detail="Purchase request not found")
    pr.status = payload.status
    db.commit()
    db.refresh(pr)
    return _enrich(pr)
