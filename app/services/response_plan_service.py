import logging
from typing import Callable

from sqlalchemy.orm import Session

from app.models import Incident, ResponsePlan, ResponsePlanAction
from app.models.constants import ResponsePlanStatus
from app.schemas import ResponsePlanGenerationResult


logger = logging.getLogger(__name__)


class ResponsePlanService:
    def __init__(self, session_factory: Callable[..., Session]):
        self.session_factory: Callable[..., Session] = session_factory

    def create_from_generation_result(
        self,
        incident_idx: int,
        thread_id: str,
        generation_result: ResponsePlanGenerationResult,
    ) -> ResponsePlan:
        with self.session_factory() as db:
            incident = db.query(Incident).filter(Incident.idx == incident_idx).first()
            if incident is None:
                raise ValueError("Incident not found")

            existing = self._get_active_plan(db, incident_idx)
            if existing is not None:
                return existing

            response_plan = self._create_response_plan(
                db=db,
                incident_idx=incident_idx,
                thread_id=thread_id,
                generation_result=generation_result,
            )
            logger.info(
                "Response plan created - incident_idx=%s response_plan_idx=%s",
                incident_idx,
                response_plan.idx,
            )
            return response_plan

    def create_from_draft(
        self,
        incident_idx: int,
        thread_id: str,
        draft: ResponsePlanGenerationResult,
    ) -> ResponsePlan:
        return self.create_from_generation_result(
            incident_idx=incident_idx,
            thread_id=thread_id,
            generation_result=draft,
        )

    def get_by_incident(self, incident_idx: int) -> ResponsePlan | None:
        with self.session_factory() as db:
            return (
                db.query(ResponsePlan)
                .filter(ResponsePlan.incident_idx == incident_idx)
                .order_by(ResponsePlan.created_at.desc())
                .first()
            )

    def get_by_idx(self, response_plan_idx: int) -> ResponsePlan | None:
        with self.session_factory() as db:
            return (
                db.query(ResponsePlan)
                .filter(ResponsePlan.idx == response_plan_idx)
                .first()
            )

    def approve(self, response_plan_idx: int) -> ResponsePlan:
        with self.session_factory() as db:
            response_plan = self._get_response_plan_or_raise(db, response_plan_idx)
            if response_plan.status != ResponsePlanStatus.PENDING.value:
                raise ValueError("Only pending response plans can be approved")

            response_plan.status = ResponsePlanStatus.APPROVED.value
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
            response_plan.denied_reason = denied_reason
            db.commit()
            db.refresh(response_plan)
            return response_plan

    def update_status(self, response_plan_idx: int, status: str) -> ResponsePlan:
        with self.session_factory() as db:
            response_plan = self._get_response_plan_or_raise(db, response_plan_idx)
            response_plan.status = status
            db.commit()
            db.refresh(response_plan)
            return response_plan

    def _create_response_plan(
        self,
        db: Session,
        incident_idx: int,
        thread_id: str,
        generation_result: ResponsePlanGenerationResult,
    ) -> ResponsePlan:
        response_plan = ResponsePlan(
            incident_idx=incident_idx,
            thread_id=thread_id,
            summary=generation_result.summary,
            status=ResponsePlanStatus.PENDING.value,
        )
        db.add(response_plan)
        db.flush()

        for index, action in enumerate(generation_result.actions, start=1):
            db.add(
                ResponsePlanAction(
                    response_plan_idx=response_plan.idx,
                    execution_order=action.execution_order or index,
                    tool_name=action.tool_name,
                    arguments=action.arguments,
                    reason=action.reason,
                )
            )

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
