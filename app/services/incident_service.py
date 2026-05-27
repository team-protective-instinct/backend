import logging
from datetime import datetime
from math import ceil
from typing import Callable

from sqlalchemy import String, cast as sql_cast, func, or_
from sqlalchemy.orm import Session

from app.dtos import IncidentListResult, IncidentSummaryResult
from app.models import Incident
from app.models.constants import (
    IncidentAnalysisStatus,
    IncidentResponsePlanStatus,
    IncidentStatus,
)
from app.schemas import AnalysisReport


logger = logging.getLogger(__name__)


class IncidentService:
    def __init__(self, session_factory: Callable[..., Session]):
        self.session_factory: Callable[..., Session] = session_factory

    def create_from_webhook(
        self,
        title: str,
        severity: str | None,
        evidence_logs: str,
        raw_payload: dict[str, object],
    ) -> Incident:
        incident = Incident(
            thread_id=None,
            title=title,
            status=IncidentStatus.ANALYZING.value,
            evidence_logs=evidence_logs,
            raw_payload=raw_payload,
            severity=severity,
            analysis_status=IncidentAnalysisStatus.PENDING.value,
            analysis_attempts=0,
            analysis_last_error=None,
            response_plan_status=None,
            response_plan_attempts=0,
            response_plan_last_error=None,
        )
        with self.session_factory() as db:
            db.add(incident)
            db.commit()
            db.refresh(incident)
            return incident

    def claim_pending_analysis_batch(self, limit: int = 5) -> list[Incident]:
        with self.session_factory() as db:
            incidents = (
                db.query(Incident)
                .filter(
                    Incident.analysis_status == IncidentAnalysisStatus.PENDING.value
                )
                .order_by(Incident.created_at.asc())
                .with_for_update(skip_locked=True)
                .limit(limit)
                .all()
            )
            for incident in incidents:
                incident.analysis_status = IncidentAnalysisStatus.PROCESSING.value
                incident.analysis_attempts += 1
                incident.analysis_last_error = None
            db.commit()
            for incident in incidents:
                db.refresh(incident)
            return incidents

    def mark_analysis_succeeded(
        self,
        incident_idx: int,
        thread_id: str,
        analysis: AnalysisReport,
    ) -> Incident:
        with self.session_factory() as db:
            incident = self._get_incident_or_raise(db, incident_idx)
            incident.thread_id = thread_id
            incident.analysis_result = analysis.model_dump()
            incident.is_identified_threat = analysis.is_true_positive
            incident.severity = analysis.severity
            incident.attack_type = analysis.attack_type
            incident.confidence_score = analysis.confidence_score
            incident.attacker_ip = analysis.attack_ip
            incident.analysis_summary = analysis.analysis_summary
            incident.analysis_last_error = None

            if analysis.is_true_positive:
                incident.status = IncidentStatus.PENDING_REVIEW.value
                incident.analysis_status = IncidentAnalysisStatus.COMPLETED.value
                incident.response_plan_status = IncidentResponsePlanStatus.PENDING.value
                incident.response_plan_last_error = None
            else:
                incident.status = IncidentStatus.RESOLVED.value
                incident.analysis_status = IncidentAnalysisStatus.COMPLETED.value
                incident.response_plan_status = None

            db.commit()
            db.refresh(incident)
            return incident

    def mark_analysis_failed(self, incident_idx: int, error: Exception) -> None:
        with self.session_factory() as db:
            incident = self._get_incident_or_raise(db, incident_idx)
            incident.analysis_status = (
                IncidentAnalysisStatus.FAILED.value
                if incident.analysis_attempts >= 3
                else IncidentAnalysisStatus.PENDING.value
            )
            incident.analysis_last_error = str(error)
            db.commit()

    def claim_pending_response_plan_batch(self, limit: int = 5) -> list[Incident]:
        with self.session_factory() as db:
            incidents = (
                db.query(Incident)
                .filter(
                    Incident.analysis_status == IncidentAnalysisStatus.COMPLETED.value,
                    Incident.is_identified_threat.is_(True),
                    Incident.response_plan_status
                    == IncidentResponsePlanStatus.PENDING.value,
                )
                .order_by(Incident.modified_at.asc())
                .with_for_update(skip_locked=True)
                .limit(limit)
                .all()
            )
            for incident in incidents:
                incident.response_plan_status = (
                    IncidentResponsePlanStatus.PROCESSING.value
                )
                incident.response_plan_attempts += 1
                incident.response_plan_last_error = None
            db.commit()
            for incident in incidents:
                db.refresh(incident)
            return incidents

    def mark_response_plan_succeeded(self, incident_idx: int) -> None:
        with self.session_factory() as db:
            incident = self._get_incident_or_raise(db, incident_idx)
            incident.response_plan_status = IncidentResponsePlanStatus.COMPLETED.value
            incident.response_plan_last_error = None
            db.commit()

    def mark_response_plan_failed(self, incident_idx: int, error: Exception) -> None:
        with self.session_factory() as db:
            incident = self._get_incident_or_raise(db, incident_idx)
            incident.response_plan_status = (
                IncidentResponsePlanStatus.FAILED.value
                if incident.response_plan_attempts >= 3
                else IncidentResponsePlanStatus.PENDING.value
            )
            incident.response_plan_last_error = str(error)
            db.commit()

    def create_incident_from_analysis(
        self,
        db: Session,
        title: str,
        raw_log: str,
        analysis_data: dict[str, object] | None,
        is_threat: bool,
        thread_id: str,
        severity: str | None = None,
        attack_type: str | None = None,
        confidence_score: float | None = None,
        attacker_ip: str | None = None,
        analysis_summary: str | None = None,
    ) -> Incident:
        incident = Incident(
            thread_id=thread_id,
            title=title,
            status=IncidentStatus.PENDING_REVIEW.value
            if is_threat
            else IncidentStatus.RESOLVED.value,
            evidence_logs=raw_log,
            analysis_result=analysis_data,
            is_identified_threat=is_threat,
            severity=severity,
            attack_type=attack_type,
            confidence_score=confidence_score,
            attacker_ip=attacker_ip,
            analysis_summary=analysis_summary,
            analysis_status=IncidentAnalysisStatus.COMPLETED.value,
            response_plan_status=IncidentResponsePlanStatus.PENDING.value
            if is_threat
            else None,
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)
        return incident

    def get_pending_incidents(self) -> list[Incident]:
        with self.session_factory() as db:
            incidents = (
                db.query(Incident)
                .filter(Incident.status == IncidentStatus.PENDING_REVIEW.value)
                .all()
            )
            return incidents

    def get_incidents(
        self,
        page: int = 1,
        limit: int = 20,
        status: IncidentStatus | None = None,
        severity: str | None = None,
        q: str | None = None,
    ) -> IncidentListResult:
        page = max(page, 1)
        limit = min(max(limit, 1), 100)

        with self.session_factory() as db:
            query = db.query(Incident)

            if status:
                query = query.filter(Incident.status == status.value)
            if severity:
                query = query.filter(Incident.severity == severity)
            if q:
                pattern = f"%{q.strip()}%"
                query = query.filter(
                    or_(
                        Incident.attack_type.ilike(pattern),
                        Incident.attacker_ip.ilike(pattern),
                        Incident.analysis_summary.ilike(pattern),
                        Incident.evidence_logs.ilike(pattern),
                        sql_cast(Incident.analysis_result, String).ilike(pattern),
                    )
                )

            total = int(query.with_entities(func.count(Incident.idx)).scalar() or 0)
            incidents = (
                query.order_by(Incident.created_at.desc())
                .offset((page - 1) * limit)
                .limit(limit)
                .all()
            )

            return IncidentListResult(
                items=incidents,
                page=page,
                limit=limit,
                total=total,
                total_pages=ceil(total / limit) if total else 0,
            )

    def get_incident_by_idx(self, incident_idx: int) -> Incident | None:
        with self.session_factory() as db:
            return db.query(Incident).filter(Incident.idx == incident_idx).first()

    def get_summary(self) -> IncidentSummaryResult:
        with self.session_factory() as db:
            today_start = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            pending_count = (
                db.query(func.count(Incident.idx))
                .filter(Incident.status == IncidentStatus.PENDING_REVIEW.value)
                .scalar()
                or 0
            )

            today_count = (
                db.query(func.count(Incident.idx))
                .filter(Incident.created_at >= today_start)
                .scalar()
                or 0
            )

            resolved_count = (
                db.query(func.count(Incident.idx))
                .filter(Incident.status == IncidentStatus.RESOLVED.value)
                .scalar()
                or 0
            )

            recent_pending = (
                db.query(Incident)
                .filter(Incident.status == IncidentStatus.PENDING_REVIEW.value)
                .order_by(Incident.created_at.desc())
                .limit(5)
                .all()
            )

            return IncidentSummaryResult(
                pending_count=pending_count,
                today_count=today_count,
                resolved_count=resolved_count,
                recent_pending=recent_pending,
            )

    def _get_incident_or_raise(self, db: Session, incident_idx: int) -> Incident:
        incident = db.query(Incident).filter(Incident.idx == incident_idx).first()
        if incident is None:
            raise ValueError("Incident not found")
        return incident
