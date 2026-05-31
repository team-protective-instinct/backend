from typing import Callable

from sqlalchemy.orm import Session

from app.models import ResponsePlanAction
from app.models.constants import ResponsePlanActionStatus


class ResponsePlanActionService:
    def __init__(self, session_factory: Callable[..., Session]):
        self.session_factory = session_factory

    def get_pending_action_ids(self, response_plan_idx: int) -> list[int]:
        with self.session_factory() as db:
            actions = (
                db.query(ResponsePlanAction)
                .filter(
                    ResponsePlanAction.response_plan_idx == response_plan_idx,
                    ResponsePlanAction.status == ResponsePlanActionStatus.PENDING.value,
                )
                .order_by(ResponsePlanAction.execution_order.asc())
                .all()
            )
            return [action.idx for action in actions]

    def update_status(
        self,
        action_idx: int,
        status: str,
        result: dict[str, object] | None = None,
    ) -> ResponsePlanAction:
        with self.session_factory() as db:
            action = self._get_action(db, action_idx)
            action.status = status
            action.result = result
            db.commit()
            db.refresh(action)
            db.expunge(action)
            return action

    def skip_pending_actions(self, response_plan_idx: int, reason: str) -> None:
        with self.session_factory() as db:
            db.query(ResponsePlanAction).filter(
                ResponsePlanAction.response_plan_idx == response_plan_idx,
                ResponsePlanAction.status == ResponsePlanActionStatus.PENDING.value,
            ).update(
                {
                    ResponsePlanAction.status: ResponsePlanActionStatus.SKIPPED.value,
                    ResponsePlanAction.result: {
                        "ok": False,
                        "status": "skipped",
                        "reason": reason,
                    },
                },
                synchronize_session=False,
            )
            db.commit()

    def _get_action(self, db: Session, action_idx: int) -> ResponsePlanAction:
        action = (
            db.query(ResponsePlanAction)
            .filter(ResponsePlanAction.idx == action_idx)
            .first()
        )
        if action is None:
            raise ValueError("Response plan action not found")
        return action
