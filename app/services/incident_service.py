import json
import logging
import uuid
from math import ceil
from typing import Callable, cast
from langchain_core.messages import HumanMessage
from sqlalchemy import String, cast as sql_cast, func, or_
from sqlalchemy.orm import Session
from app.dtos import IncidentListResult, IncidentSummaryResult
from app.models import Incident
from app.models.constants import IncidentStatus
from app.agents.incident_analyzer.state import AgentState
from app.agents.incident_analyzer.prompt import LOG_ANALYSIS_REQUEST_PREFIX
from app.agents.incident_analyzer.agent import ThreatAnalyzerAgent
from datetime import datetime


logger = logging.getLogger(__name__)


class IncidentService:
    def __init__(
        self, session_factory: Callable[..., Session], threat_agent: ThreatAnalyzerAgent
    ):
        self.session_factory: Callable[..., Session] = session_factory
        self.threat_agent: ThreatAnalyzerAgent = threat_agent

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
            status=IncidentStatus.PENDING_REVIEW
            if is_threat
            else IncidentStatus.RESOLVED,
            evidence_logs=raw_log,
            analysis_result=analysis_data,
            is_identified_threat=is_threat,
            severity=severity,
            attack_type=attack_type,
            confidence_score=confidence_score,
            attacker_ip=attacker_ip,
            analysis_summary=analysis_summary,
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)
        return incident

    def get_pending_incidents(self) -> list[Incident]:
        with self.session_factory() as db:
            incidents = (
                db.query(Incident)
                .filter(Incident.status == IncidentStatus.PENDING_REVIEW)
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
                .filter(Incident.status == IncidentStatus.PENDING_REVIEW)
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
                .filter(Incident.status == IncidentStatus.RESOLVED)
                .scalar()
                or 0
            )

            critical_count = (
                db.query(func.count(Incident.idx))
                .filter(Incident.severity == "critical")
                .scalar()
                or 0
            )

            recent_pending = (
                db.query(Incident)
                .filter(Incident.status == IncidentStatus.PENDING_REVIEW)
                .order_by(Incident.created_at.desc())
                .limit(5)
                .all()
            )

            return IncidentSummaryResult(
                pending_count=pending_count,
                today_count=today_count,
                resolved_count=resolved_count,
                critical_count=critical_count,
                recent_pending=recent_pending,
            )

    def approve_incident(self, incident_idx: int) -> None:
        # TODO: Implement approve logic
        _ = incident_idx
        pass

    def deny_incident(self, incident_idx: int) -> None:
        # TODO: Implement deny logic
        _ = incident_idx
        pass

    def incident_analysis(self, log_text: str):
        """
        Run threat analysis and return the result (State).
        Automatically records the results in the database with a thread_id.
        """
        thread_id = str(uuid.uuid4())

        initial_state: AgentState = {
            "messages": [
                HumanMessage(content=f"{LOG_ANALYSIS_REQUEST_PREFIX}{log_text}")
            ],
            "context": {"source": "log_analytics_service"},
        }

        logger.info(f"[Starting Threat Analysis - Thread ID: {thread_id}]")

        # Use invoke to get the final state
        final_state = cast(
            AgentState,
            self.threat_agent.invoke(
                initial_state, config={"configurable": {"thread_id": thread_id}}
            ),
        )

        analysis_dict: dict[str, object] | None = None
        is_threat = False
        severity = None
        attack_type = None
        confidence_score = None
        attacker_ip = None
        analysis_summary = None

        if "analysis_result" in final_state:
            analysis = final_state["analysis_result"]
            analysis_dict = cast(dict[str, object], analysis.model_dump())
            is_threat = analysis.is_true_positive
            severity = analysis.severity
            attack_type = analysis.attack_type
            confidence_score = analysis.confidence_score
            attacker_ip = analysis.attack_ip
            analysis_summary = analysis.analysis_summary

            logger.info("[Threat Analysis Completed]")
            logger.info(
                f" - Verdict: {'True Positive' if is_threat else 'False Positive'}"
            )
            logger.info(f" - Severity: {severity}")
            logger.info(f" - Confidence Score: {confidence_score}")
            logger.info(f" - Attack Type: {attack_type}")
            logger.info(f" - Primary Attacker IP: {attacker_ip}")
            logger.info(f" - Summary: {analysis.analysis_summary}")

            logger.debug(
                json.dumps(
                    analysis_dict,
                    ensure_ascii=False,
                    indent=2,
                )
            )

        logger.info("Storing analysis results in the database...")

        with self.session_factory() as db:
            try:
                _ = self.create_incident_from_analysis(
                    db=db,
                    title=f"Auto Log Analysis - {thread_id[:8]}",
                    raw_log=log_text,
                    analysis_data=analysis_dict,
                    is_threat=is_threat,
                    thread_id=thread_id,
                    severity=severity,
                    attack_type=attack_type,
                    confidence_score=confidence_score,
                    attacker_ip=attacker_ip,
                    analysis_summary=analysis_summary,
                )
                logger.info(f"DB Storage Completed (Thread ID: {thread_id})")
            except Exception as e:
                logger.error(f"DB Storage Error: {e}")

        result_state: dict[str, object] = dict(final_state)
        result_state["thread_id"] = thread_id
        return result_state
