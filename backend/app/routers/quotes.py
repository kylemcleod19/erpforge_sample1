import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.product import Product
from app.models.quote import Quote, QuoteLineItem
from app.schemas.order import OrderOut
from app.schemas.quote import (
    QuoteCreate,
    QuoteLineItemCreate,
    QuoteLineItemOut,
    QuoteOut,
    QuoteStatusTransition,
    QuoteUpdate,
)
from app.services.order_service import convert_quote_to_order

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/quotes", tags=["quotes"])

VALID_TRANSITIONS: dict[str, list[str]] = {
    "draft": ["review", "lost"],
    "review": ["approved", "draft", "lost"],
    "approved": ["sent", "lost"],
    "sent": ["won", "lost"],
    "won": [],
    "lost": [],
}


def _enrich_line_item(li: QuoteLineItem) -> QuoteLineItemOut:
    return QuoteLineItemOut(
        id=li.id,
        quote_id=li.quote_id,
        product_id=li.product_id,
        product_name=li.product.name if li.product else None,
        product_sku=li.product.sku if li.product else None,
        quantity=li.quantity,
        unit_price=li.unit_price,
        lead_time_days=li.lead_time_days,
        subtotal=li.subtotal,
    )


@router.get("", response_model=list[QuoteOut])
def list_quotes(status: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Quote)
    if status:
        q = q.filter(Quote.status == status)
    return q.order_by(Quote.created_at.desc()).all()


@router.post("", response_model=QuoteOut, status_code=201)
def create_quote(payload: QuoteCreate, db: Session = Depends(get_db)):
    quote = Quote(**payload.model_dump())
    db.add(quote)
    db.commit()
    db.refresh(quote)
    return quote


@router.get("/{quote_id}", response_model=QuoteOut)
def get_quote(quote_id: int, db: Session = Depends(get_db)):
    quote = db.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote


@router.put("/{quote_id}", response_model=QuoteOut)
def update_quote(quote_id: int, payload: QuoteUpdate, db: Session = Depends(get_db)):
    quote = db.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    if quote.status in ("won", "lost"):
        raise HTTPException(status_code=400, detail=f"Cannot edit a {quote.status} quote")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(quote, field, value)
    db.commit()
    db.refresh(quote)
    return quote


@router.post("/{quote_id}/line-items", response_model=QuoteLineItemOut, status_code=201)
def add_line_item(quote_id: int, payload: QuoteLineItemCreate, db: Session = Depends(get_db)):
    quote = db.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    if quote.status in ("won", "lost"):
        raise HTTPException(status_code=400, detail=f"Cannot modify a {quote.status} quote")
    if not db.get(Product, payload.product_id):
        raise HTTPException(status_code=404, detail="Product not found")

    li = QuoteLineItem(quote_id=quote_id, **payload.model_dump())
    db.add(li)
    db.commit()
    db.refresh(li)
    return _enrich_line_item(li)


@router.delete("/{quote_id}/line-items/{item_id}", status_code=204)
def remove_line_item(quote_id: int, item_id: int, db: Session = Depends(get_db)):
    quote = db.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    if quote.status in ("won", "lost"):
        raise HTTPException(status_code=400, detail=f"Cannot modify a {quote.status} quote")

    li = db.query(QuoteLineItem).filter(
        QuoteLineItem.id == item_id,
        QuoteLineItem.quote_id == quote_id,
    ).first()
    if not li:
        raise HTTPException(status_code=404, detail="Line item not found")
    db.delete(li)
    db.commit()


@router.post("/{quote_id}/status", response_model=QuoteOut)
def transition_status(quote_id: int, payload: QuoteStatusTransition, db: Session = Depends(get_db)):
    quote = db.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    allowed = VALID_TRANSITIONS.get(quote.status, [])
    if payload.status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from '{quote.status}' to '{payload.status}'. Allowed: {allowed}",
        )

    quote.status = payload.status
    db.commit()
    db.refresh(quote)
    return quote


@router.post("/{quote_id}/convert", response_model=OrderOut)
def convert_quote(quote_id: int, db: Session = Depends(get_db)):
    try:
        order = convert_quote_to_order(quote_id, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return order
