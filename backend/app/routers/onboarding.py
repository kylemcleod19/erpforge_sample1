from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.onboarding_service import get_or_create_progress, get_progress_response, refresh_milestones

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


@router.get("/progress")
def progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_progress_response(current_user, db)


@router.post("/dismiss")
def dismiss(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prog = get_or_create_progress(current_user, db)
    prog.dismissed = True
    db.commit()
    return {"ok": True}


@router.post("/refresh")
def refresh(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_progress_response(current_user, db)
