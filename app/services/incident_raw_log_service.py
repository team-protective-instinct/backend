from typing import Callable

from sqlalchemy.orm import Session

from app.models import IncidentRawLog
from app.models.constants import IncidentRawLogSourceType


RawLogSourceTypeValue = IncidentRawLogSourceType | str


class IncidentRawLogService:
    def __init__(self, session_factory: Callable[..., Session]):
        self.session_factory: Callable[..., Session] = session_factory

    def create_for_incident(
        self,
        incident_idx: int,
        raw_payload: dict[str, object] | None,
        source_type: RawLogSourceTypeValue = IncidentRawLogSourceType.WEBHOOK,
    ) -> IncidentRawLog:
        with self.session_factory() as db:
            raw_log = self.create_for_incident_in_session(
                db=db,
                incident_idx=incident_idx,
                raw_payload=raw_payload,
                source_type=source_type,
            )
            db.commit()
            db.refresh(raw_log)
            return raw_log

    def create_for_incident_in_session(
        self,
        db: Session,
        incident_idx: int,
        raw_payload: dict[str, object] | None,
        source_type: RawLogSourceTypeValue = IncidentRawLogSourceType.WEBHOOK,
    ) -> IncidentRawLog:
        raw_log = IncidentRawLog(
            incident_idx=incident_idx,
            source_type=self._source_type_value(source_type),
            raw_payload=raw_payload,
        )
        db.add(raw_log)
        return raw_log

    def get_latest_by_incident(
        self,
        incident_idx: int,
        source_type: RawLogSourceTypeValue | None = IncidentRawLogSourceType.WEBHOOK,
    ) -> IncidentRawLog | None:
        with self.session_factory() as db:
            return self.get_latest_by_incident_in_session(db, incident_idx, source_type)

    def get_latest_by_incident_in_session(
        self,
        db: Session,
        incident_idx: int,
        source_type: RawLogSourceTypeValue | None = IncidentRawLogSourceType.WEBHOOK,
    ) -> IncidentRawLog | None:
        query = db.query(IncidentRawLog).filter(
            IncidentRawLog.incident_idx == incident_idx
        )
        if source_type is not None:
            query = query.filter(
                IncidentRawLog.source_type == self._source_type_value(source_type)
            )
        return query.order_by(
            IncidentRawLog.created_at.desc(), IncidentRawLog.idx.desc()
        ).first()

    def get_by_incident(self, incident_idx: int) -> list[IncidentRawLog]:
        with self.session_factory() as db:
            return self.get_by_incident_in_session(db, incident_idx)

    def get_by_incident_in_session(
        self, db: Session, incident_idx: int
    ) -> list[IncidentRawLog]:
        return (
            db.query(IncidentRawLog)
            .filter(IncidentRawLog.incident_idx == incident_idx)
            .order_by(IncidentRawLog.created_at.asc(), IncidentRawLog.idx.asc())
            .all()
        )

    def _source_type_value(self, source_type: RawLogSourceTypeValue) -> str:
        if isinstance(source_type, IncidentRawLogSourceType):
            return source_type.value
        return source_type
