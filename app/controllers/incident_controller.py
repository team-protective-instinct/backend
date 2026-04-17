from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db


router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("/pending")
def get_pending_incidents(db: Session = Depends(get_db)):
    pass


@router.get("/{incident_idx}")
def get_incident_by_idx(incident_idx: int, db: Session = Depends(get_db)):
    pass


@router.post("/{incident_id}/approve")
def approve_incident(incident_id: int, db: Session = Depends(get_db)):
    pass


@router.post("/{incident_id}/deny")
def deny_incident(incident_id: int, db: Session = Depends(get_db)):
    pass
