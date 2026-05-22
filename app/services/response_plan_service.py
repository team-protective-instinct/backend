import logging
import uuid
from datetime import datetime
from typing import Callable, cast

from sqlalchemy.orm import Session

from app.agents.response_plan_agent.agent import ResponsePlanAgent
from app.agents.response_plan_agent.state import ResponsePlanState
from app.models import Incident, ResponsePlan
from app.models.constants import ResponsePlanStatus
from app.schemas import ResponsePlanDraft
from app.services.playbook_service import PlaybookService


logger = logging.getLogger(__name__)


class ResponsePlanService:
    def __init__(
        self,
        session_factory: Callable[..., Session],
        response_plan_agent: ResponsePlanAgent,
        playbook_service: PlaybookService,
    ):
        self.session_factory: Callable[..., Session] = session_factory
        self.response_plan_agent: ResponsePlanAgent = response_plan_agent
        self.playbook_service: PlaybookService = playbook_service

    def create_for_incident(self, incident_idx: int) -> ResponsePlan:
        with self.session_factory() as db:
            incident = db.query(Incident).filter(Incident.idx == incident_idx).first()
            if incident is None:
                raise ValueError("Incident not found")

            existing = self._get_active_plan(db, incident_idx)
            if existing is not None:
                return existing

            query = self._build_retrieval_query(incident)
            context = self._build_agent_context(incident)

        retrieved_chunks = self.playbook_service.retrieve_relevant_chunks(
            query=query,
            limit=5,
        )

        thread_id = f"response-plan:{incident_idx}:{uuid.uuid4()}"
        initial_state: ResponsePlanState = {
            "context": context,
            "retrieved_chunks": [
                self.playbook_service.retrieval_result_to_dict(chunk)
                for chunk in retrieved_chunks
            ],
        }
        final_state = cast(
            ResponsePlanState,
            self.response_plan_agent.invoke(
                initial_state,
                config={"configurable": {"thread_id": thread_id}},
            ),
        )
        draft = final_state.get("response_plan")
        if draft is None:
            raise RuntimeError("ResponsePlanAgent did not generate a response plan")

        with self.session_factory() as db:
            response_plan = self._create_response_plan(
                db=db,
                incident_idx=incident_idx,
                thread_id=thread_id,
                draft=draft,
            )
            logger.info(
                "Response plan created - incident_idx=%s response_plan_idx=%s",
                incident_idx,
                response_plan.idx,
            )
            return response_plan

    def get_by_incident(self, incident_idx: int) -> ResponsePlan | None:
        with self.session_factory() as db:
            return (
                db.query(ResponsePlan)
                .filter(ResponsePlan.incident_idx == incident_idx)
                .order_by(ResponsePlan.created_at.desc())
                .first()
            )

    def approve(self, response_plan_idx: int) -> ResponsePlan:
        with self.session_factory() as db:
            response_plan = self._get_response_plan_or_raise(db, response_plan_idx)
            if response_plan.status != ResponsePlanStatus.PENDING.value:
                raise ValueError("Only pending response plans can be approved")

            response_plan.status = ResponsePlanStatus.APPROVED.value
            response_plan.approved_at = datetime.now()
            response_plan.denied_at = None
            response_plan.denied_reason = None
            db.commit()
            db.refresh(response_plan)
            return response_plan

    def deny(self, response_plan_idx: int, denied_reason: str) -> ResponsePlan:
        with self.session_factory() as db:
            response_plan = self._get_response_plan_or_raise(db, response_plan_idx)
            if response_plan.status != ResponsePlanStatus.PENDING.value:
                raise ValueError("Only pending response plans can be denied")

            response_plan.status = ResponsePlanStatus.DENIED.value
            response_plan.denied_at = datetime.now()
            response_plan.denied_reason = denied_reason
            db.commit()
            db.refresh(response_plan)
            return response_plan

    def _create_response_plan(
        self,
        db: Session,
        incident_idx: int,
        thread_id: str,
        draft: ResponsePlanDraft,
    ) -> ResponsePlan:
        response_plan = ResponsePlan(
            incident_idx=incident_idx,
            thread_id=thread_id,
            summary=draft.summary,
            rationale=draft.rationale,
            plan_text=draft.plan_text,
            status=ResponsePlanStatus.PENDING.value,
        )
        db.add(response_plan)
        db.commit()
        db.refresh(response_plan)
        return response_plan

    def _get_active_plan(self, db: Session, incident_idx: int) -> ResponsePlan | None:
        active_statuses = [
            ResponsePlanStatus.PENDING.value,
            ResponsePlanStatus.APPROVED.value,
            ResponsePlanStatus.EXECUTING.value,
            ResponsePlanStatus.EXECUTED.value,
        ]
        return (
            db.query(ResponsePlan)
            .filter(
                ResponsePlan.incident_idx == incident_idx,
                ResponsePlan.status.in_(active_statuses),
            )
            .order_by(ResponsePlan.created_at.desc())
            .first()
        )

    def _get_response_plan_or_raise(
        self, db: Session, response_plan_idx: int
    ) -> ResponsePlan:
        response_plan = (
            db.query(ResponsePlan).filter(ResponsePlan.idx == response_plan_idx).first()
        )
        if response_plan is None:
            raise ValueError("Response plan not found")
        return response_plan

    def _build_retrieval_query(self, incident: Incident) -> str:
        context = self._build_agent_context(incident)
        parts = [
            str(context.get("attack_type") or ""),
            str(context.get("severity") or ""),
            str(context.get("analysis_summary") or ""),
            " ".join(cast(list[str], context.get("target_uris") or [])),
            " ".join(cast(list[str], context.get("suspicious_payloads") or [])),
            str(context.get("raw_log") or ""),
        ]
        return "\n".join(part for part in parts if part.strip())

    def _build_agent_context(self, incident: Incident) -> dict[str, object]:
        analysis = incident.analysis_result if isinstance(incident.analysis_result, dict) else {}
        raw_log = incident.evidence_logs or ""
        return {
            "incident_idx": incident.idx,
            "title": incident.title,
            "severity": incident.severity,
            "attack_type": incident.attack_type,
            "confidence_score": incident.confidence_score,
            "attacker_ip": incident.attacker_ip,
            "analysis_summary": incident.analysis_summary,
            "analysis_result": analysis,
            "target_uris": self._get_string_list(analysis, "target_uris"),
            "suspicious_payloads": self._get_string_list(analysis, "suspicious_payloads"),
            "raw_log": raw_log[:6000],
            "created_at": incident.created_at.isoformat(),
        }

    def _get_string_list(self, data: dict[str, object], key: str) -> list[str]:
        value = data.get(key)
        if not isinstance(value, list):
            return []
        return [str(item) for item in value]
