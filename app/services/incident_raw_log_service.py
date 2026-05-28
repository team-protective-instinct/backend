from typing import Callable

from sqlalchemy.orm import Session

from app.models import IncidentRawLog


class IncidentRawLogService:
    def __init__(self, session_factory: Callable[..., Session]):
        self.session_factory: Callable[..., Session] = session_factory

    def create_for_incident(
        self,
        incident_idx: int,
        evidence_logs: str,
        raw_payload: dict[str, object] | None,
    ) -> IncidentRawLog:
        with self.session_factory() as db:
            raw_log = self.create_for_incident_in_session(
                db=db,
                incident_idx=incident_idx,
                evidence_logs=evidence_logs,
                raw_payload=raw_payload,
            )
            db.commit()
            db.refresh(raw_log)
            return raw_log

    def create_for_incident_in_session(
        self,
        db: Session,
        incident_idx: int,
        evidence_logs: str,
        raw_payload: dict[str, object] | None,
    ) -> IncidentRawLog:
        raw_log = IncidentRawLog(
            incident_idx=incident_idx,
            evidence_logs=evidence_logs,
            raw_payload=raw_payload,
        )
        db.add(raw_log)
        return raw_log

    def get_latest_by_incident(self, incident_idx: int) -> IncidentRawLog | None:
        with self.session_factory() as db:
            return self.get_latest_by_incident_in_session(db, incident_idx)

    def get_latest_by_incident_in_session(
        self, db: Session, incident_idx: int
    ) -> IncidentRawLog | None:
        return (
            db.query(IncidentRawLog)
            .filter(IncidentRawLog.incident_idx == incident_idx)
            .order_by(IncidentRawLog.created_at.desc(), IncidentRawLog.idx.desc())
            .first()
        )
