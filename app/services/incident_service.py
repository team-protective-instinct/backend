import logging
from datetime import datetime
from math import ceil
from typing import Callable

from sqlalchemy import String, cast as sql_cast, func, or_
from sqlalchemy.orm import Session

from app.dtos import IncidentListResult, IncidentSummaryResult, IncidentWithReport
from app.models import Incident, IncidentRawLog, IncidentReport
from app.models.constants import (
    IncidentAnalysisStatus,
    IncidentResponsePlanStatus,
    IncidentStatus,
)
from app.schemas import AnalysisReport
from app.services.incident_raw_log_service import IncidentRawLogService
from app.services.incident_report_service import IncidentReportService


logger = logging.getLogger(__name__)


class IncidentService:
    def __init__(
        self,
        session_factory: Callable[..., Session],
        raw_log_service: IncidentRawLogService,
        report_service: IncidentReportService,
    ):
        self.session_factory: Callable[..., Session] = session_factory
        self.raw_log_service = raw_log_service
        self.report_service = report_service

    def create_from_webhook(
        self,
        title: str,
        severity: str | None,
        evidence_logs: str,
        raw_payload: dict[str, object],
    ) -> Incident:
        incident = Incident(
            title=title,
            status=IncidentStatus.ANALYZING.value,
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
            db.flush()
            self.raw_log_service.create_for_incident_in_session(
                db=db,
                incident_idx=incident.idx,
                evidence_logs=evidence_logs,
                raw_payload=raw_payload,
            )
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
            incident.is_identified_threat = analysis.is_true_positive
            incident.severity = analysis.severity
            incident.analysis_last_error = None
            self.report_service.create_from_analysis_in_session(
                db=db,
                incident_idx=incident_idx,
                thread_id=thread_id,
                analysis=analysis,
            )

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

    def get_pending_incidents(self) -> list[IncidentWithReport]:
        with self.session_factory() as db:
            incidents = (
                db.query(Incident)
                .filter(Incident.status == IncidentStatus.PENDING_REVIEW.value)
                .all()
            )
            return self._get_incidents_with_reports(db, incidents)

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
                keyword = q.strip()
                if keyword:
                    pattern = f"%{keyword}%"
                    query = query.outerjoin(
                        IncidentReport, IncidentReport.incident_idx == Incident.idx
                    ).outerjoin(
                        IncidentRawLog, IncidentRawLog.incident_idx == Incident.idx
                    )
                    query = query.filter(
                        or_(
                            IncidentReport.attack_type.ilike(pattern),
                            IncidentReport.attacker_ip.ilike(pattern),
                            IncidentReport.analysis_summary.ilike(pattern),
                            IncidentRawLog.evidence_logs.ilike(pattern),
                            sql_cast(IncidentReport.analysis_result, String).ilike(
                                pattern
                            ),
                        )
                    )

            total = int(
                query.with_entities(func.count(func.distinct(Incident.idx))).scalar()
                or 0
            )
            incidents = (
                query.distinct()
                .order_by(Incident.created_at.desc())
                .offset((page - 1) * limit)
                .limit(limit)
                .all()
            )

            return IncidentListResult(
                items=self._get_incidents_with_reports(db, incidents),
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
                recent_pending=self._get_incidents_with_reports(db, recent_pending),
            )

    def _get_incident_or_raise(self, db: Session, incident_idx: int) -> Incident:
        incident = db.query(Incident).filter(Incident.idx == incident_idx).first()
        if incident is None:
            raise ValueError("Incident not found")
        return incident

    def _get_incidents_with_reports(
        self, db: Session, incidents: list[Incident]
    ) -> list[IncidentWithReport]:
        latest_by_incident = self.report_service.get_latest_for_incidents_in_session(
            db, incidents
        )

        return [
            IncidentWithReport(
                incident=incident,
                report=latest_by_incident.get(incident.idx),
            )
            for incident in incidents
        ]
