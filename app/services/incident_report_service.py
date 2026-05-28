from typing import Callable

from sqlalchemy.orm import Session

from app.models import Incident, IncidentReport
from app.schemas import AnalysisReport


class IncidentReportService:
    def __init__(self, session_factory: Callable[..., Session]):
        self.session_factory: Callable[..., Session] = session_factory

    def create_from_analysis(
        self,
        incident_idx: int,
        thread_id: str,
        analysis: AnalysisReport,
    ) -> IncidentReport:
        with self.session_factory() as db:
            report = self.create_from_analysis_in_session(
                db=db,
                incident_idx=incident_idx,
                thread_id=thread_id,
                analysis=analysis,
            )
            db.commit()
            db.refresh(report)
            return report

    def create_from_analysis_in_session(
        self,
        db: Session,
        incident_idx: int,
        thread_id: str,
        analysis: AnalysisReport,
    ) -> IncidentReport:
        report = IncidentReport(
            incident_idx=incident_idx,
            thread_id=thread_id,
            attack_type=analysis.attack_type,
            confidence_score=analysis.confidence_score,
            attacker_ip=analysis.attack_ip,
            analysis_summary=analysis.analysis_summary,
            analysis_result=analysis.model_dump(),
        )
        db.add(report)
        return report

    def get_latest_by_incident(self, incident_idx: int) -> IncidentReport | None:
        with self.session_factory() as db:
            return self.get_latest_by_incident_in_session(db, incident_idx)

    def get_latest_by_incident_in_session(
        self, db: Session, incident_idx: int
    ) -> IncidentReport | None:
        return (
            db.query(IncidentReport)
            .filter(IncidentReport.incident_idx == incident_idx)
            .order_by(IncidentReport.created_at.desc(), IncidentReport.idx.desc())
            .first()
        )

    def get_latest_for_incidents_in_session(
        self, db: Session, incidents: list[Incident]
    ) -> dict[int, IncidentReport]:
        if not incidents:
            return {}

        incident_ids = [incident.idx for incident in incidents]
        reports = (
            db.query(IncidentReport)
            .filter(IncidentReport.incident_idx.in_(incident_ids))
            .order_by(
                IncidentReport.incident_idx.asc(),
                IncidentReport.created_at.desc(),
                IncidentReport.idx.desc(),
            )
            .all()
        )
        latest_by_incident: dict[int, IncidentReport] = {}
        for report in reports:
            if report.incident_idx not in latest_by_incident:
                latest_by_incident[report.incident_idx] = report
        return latest_by_incident
