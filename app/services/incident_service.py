from sqlalchemy.orm import Session
from app.models import Incident


def create_incident(db: Session, title: str, description: str):
    incident = Incident(title=title, description=description)
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def create_incident_from_analysis(
    db: Session,
    title: str,
    raw_log: str,
    verdict_data: dict,
    report_data: dict,
    is_threat: bool,
    thread_id: str
) -> Incident:
    incident = Incident(
        thread_id=thread_id,
        title=title,
        status="completed",
        evidence_logs=raw_log,
        verdict_json=verdict_data,
        report_json=report_data,
        is_identified_threat=is_threat
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def get_pending_incidents(db: Session):
    return db.query(Incident).filter(Incident.status == "pending").all()


def get_incident_by_idx(db: Session, incident_idx: int):
    return db.query(Incident).filter(Incident.idx == incident_idx).first()


def approve_incident(db: Session, incident_id: int):
    pass


def deny_incident(db: Session, incident_id: int):
    pass
