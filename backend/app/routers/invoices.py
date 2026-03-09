from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.invoice import Invoice
from app.schemas.invoice import InvoiceOut, InvoiceStatusUpdate

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("", response_model=list[InvoiceOut])
def list_invoices(db: Session = Depends(get_db)):
    return db.query(Invoice).order_by(Invoice.created_at.desc()).all()


@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.patch("/{invoice_id}/status", response_model=InvoiceOut)
def update_invoice_status(
    invoice_id: int,
    payload: InvoiceStatusUpdate,
    db: Session = Depends(get_db),
):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    invoice.status = payload.status
    db.commit()
    db.refresh(invoice)
    return invoice
