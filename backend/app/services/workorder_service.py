from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.manufacturing import ProductRouting, WorkOrder, WorkOrderLog


def _get_routing(product_id: int, db: Session) -> list[ProductRouting]:
    return (
        db.query(ProductRouting)
        .filter(ProductRouting.product_id == product_id)
        .order_by(ProductRouting.sequence)
        .all()
    )


def advance_station(work_order_id: int, notes: str | None, operator: str | None, db: Session) -> WorkOrder:
    wo = db.get(WorkOrder, work_order_id)
    if not wo:
        raise ValueError(f"Work order {work_order_id} not found")
    if wo.status == "completed":
        raise ValueError("Work order is already completed")
    if wo.status == "queued":
        wo.status = "in_progress"

    routing = _get_routing(wo.product_id, db)
    if not routing:
        raise ValueError(f"No routing defined for product {wo.product_id}")

    current_seq = wo.current_station_sequence
    current_step = next((r for r in routing if r.sequence == current_seq), None)
    if not current_step:
        raise ValueError(f"Current station sequence {current_seq} not found in routing")

    # Log completion of current station
    log = WorkOrderLog(
        work_order_id=wo.id,
        station_id=current_step.station_id,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        notes=notes,
        operator=operator,
    )
    db.add(log)

    # Advance to next station
    sequences = sorted(r.sequence for r in routing)
    current_idx = sequences.index(current_seq)

    if current_idx + 1 < len(sequences):
        wo.current_station_sequence = sequences[current_idx + 1]
    else:
        # Already at last station — mark complete
        wo.status = "completed"

    db.commit()
    db.refresh(wo)
    return wo


def complete_work_order(work_order_id: int, notes: str | None, operator: str | None, db: Session) -> WorkOrder:
    wo = db.get(WorkOrder, work_order_id)
    if not wo:
        raise ValueError(f"Work order {work_order_id} not found")
    if wo.status == "completed":
        raise ValueError("Work order is already completed")

    routing = _get_routing(wo.product_id, db)
    if routing:
        last_seq = max(r.sequence for r in routing)
        if wo.current_station_sequence != last_seq:
            raise ValueError(
                f"Work order must be at the last station (seq={last_seq}) to complete. "
                f"Currently at seq={wo.current_station_sequence}"
            )
        # Log final station
        last_step = next(r for r in routing if r.sequence == last_seq)
        log = WorkOrderLog(
            work_order_id=wo.id,
            station_id=last_step.station_id,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            notes=notes,
            operator=operator,
        )
        db.add(log)

    wo.status = "completed"
    db.commit()
    db.refresh(wo)
    return wo
