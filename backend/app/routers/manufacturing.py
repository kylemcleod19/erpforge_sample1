from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.manufacturing import ProductRouting, WorkOrder, WorkOrderLog, WorkStation
from app.schemas.manufacturing import (
    AdvanceWorkOrderRequest,
    ProductRoutingOut,
    RoutingEntry,
    SetRoutingRequest,
    WorkOrderOut,
    WorkStationCreate,
    WorkStationOut,
    WorkStationUpdate,
    WorkOrderLogOut,
)
from app.services.workorder_service import advance_station, complete_work_order

router = APIRouter(tags=["manufacturing"])


# --- Work Stations ---

@router.get("/stations", response_model=list[WorkStationOut])
def list_stations(db: Session = Depends(get_db)):
    return db.query(WorkStation).order_by(WorkStation.sequence, WorkStation.name).all()


@router.post("/stations", response_model=WorkStationOut, status_code=201)
def create_station(payload: WorkStationCreate, db: Session = Depends(get_db)):
    station = WorkStation(**payload.model_dump())
    db.add(station)
    db.commit()
    db.refresh(station)
    return station


@router.put("/stations/{station_id}", response_model=WorkStationOut)
def update_station(station_id: int, payload: WorkStationUpdate, db: Session = Depends(get_db)):
    station = db.get(WorkStation, station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(station, field, value)
    db.commit()
    db.refresh(station)
    return station


@router.delete("/stations/{station_id}", status_code=204)
def delete_station(station_id: int, db: Session = Depends(get_db)):
    station = db.get(WorkStation, station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    db.delete(station)
    db.commit()


# --- Product Routing ---

@router.get("/products/{product_id}/routing", response_model=ProductRoutingOut)
def get_routing(product_id: int, db: Session = Depends(get_db)):
    routing = (
        db.query(ProductRouting)
        .filter(ProductRouting.product_id == product_id)
        .order_by(ProductRouting.sequence)
        .all()
    )
    return ProductRoutingOut(
        product_id=product_id,
        routing=[RoutingEntry(station_id=r.station_id, sequence=r.sequence) for r in routing],
    )


@router.put("/products/{product_id}/routing", response_model=ProductRoutingOut)
def set_routing(product_id: int, payload: SetRoutingRequest, db: Session = Depends(get_db)):
    # Replace entire routing
    db.query(ProductRouting).filter(ProductRouting.product_id == product_id).delete()

    for i, station_id in enumerate(payload.station_ids):
        station = db.get(WorkStation, station_id)
        if not station:
            db.rollback()
            raise HTTPException(status_code=404, detail=f"Station {station_id} not found")
        routing_entry = ProductRouting(
            product_id=product_id,
            station_id=station_id,
            sequence=i + 1,
        )
        db.add(routing_entry)

    db.commit()

    routing = (
        db.query(ProductRouting)
        .filter(ProductRouting.product_id == product_id)
        .order_by(ProductRouting.sequence)
        .all()
    )
    return ProductRoutingOut(
        product_id=product_id,
        routing=[RoutingEntry(station_id=r.station_id, sequence=r.sequence) for r in routing],
    )


# --- Work Orders ---

def _enrich_wo(wo: WorkOrder) -> WorkOrderOut:
    return WorkOrderOut(
        id=wo.id,
        order_id=wo.order_id,
        product_id=wo.product_id,
        product_name=wo.product.name if wo.product else None,
        product_sku=wo.product.sku if wo.product else None,
        quantity=wo.quantity,
        status=wo.status,
        current_station_sequence=wo.current_station_sequence,
        created_at=wo.created_at,
        logs=[
            WorkOrderLogOut(
                id=log.id,
                work_order_id=log.work_order_id,
                station_id=log.station_id,
                station_name=log.station.name if log.station else None,
                started_at=log.started_at,
                completed_at=log.completed_at,
                notes=log.notes,
                operator=log.operator,
            )
            for log in wo.logs
        ],
    )


@router.get("/work-orders", response_model=list[WorkOrderOut])
def list_work_orders(
    status: str | None = None,
    order_id: int | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(WorkOrder)
    if status:
        q = q.filter(WorkOrder.status == status)
    if order_id:
        q = q.filter(WorkOrder.order_id == order_id)
    return [_enrich_wo(wo) for wo in q.order_by(WorkOrder.created_at.desc()).all()]


@router.get("/work-orders/{work_order_id}", response_model=WorkOrderOut)
def get_work_order(work_order_id: int, db: Session = Depends(get_db)):
    wo = db.get(WorkOrder, work_order_id)
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    return _enrich_wo(wo)


@router.post("/work-orders/{work_order_id}/advance", response_model=WorkOrderOut)
def advance_work_order(
    work_order_id: int,
    payload: AdvanceWorkOrderRequest | None = None,
    db: Session = Depends(get_db),
):
    notes = payload.notes if payload else None
    operator = payload.operator if payload else None
    try:
        wo = advance_station(work_order_id, notes, operator, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _enrich_wo(wo)


@router.post("/work-orders/{work_order_id}/complete", response_model=WorkOrderOut)
def complete_work_order_endpoint(
    work_order_id: int,
    payload: AdvanceWorkOrderRequest | None = None,
    db: Session = Depends(get_db),
):
    notes = payload.notes if payload else None
    operator = payload.operator if payload else None
    try:
        wo = complete_work_order(work_order_id, notes, operator, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _enrich_wo(wo)
