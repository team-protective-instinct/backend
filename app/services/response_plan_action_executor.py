import json
import logging
from typing import cast
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig

from app.agents.response_plan_agent.agent import ResponsePlanAgent
from app.agents.response_plan_agent.state import ResponsePlanState
from app.agents.utils import extract_text_from_content
from app.models import ResponsePlan
from app.models.constants import ResponsePlanActionStatus, ResponsePlanStatus
from app.services.incident_service import IncidentService
from app.services.response_plan_action_service import ResponsePlanActionService
from app.services.response_plan_service import ResponsePlanService

logger = logging.getLogger(__name__)


class ResponsePlanActionExecutor:
    def __init__(
        self,
        action_service: ResponsePlanActionService,
        response_plan_service: ResponsePlanService,
        incident_service: IncidentService,
        response_plan_agent: ResponsePlanAgent,
    ):
        self.action_service = action_service
        self.response_plan_service = response_plan_service
        self.incident_service = incident_service
        self.response_plan_agent = response_plan_agent

    async def execute_pending_actions(self, response_plan_idx: int) -> None:
        pending_actions = self.action_service.get_pending_action_ids(response_plan_idx)
        if not pending_actions:
            self._mark_plan_executed_without_actions(response_plan_idx)
            return

        response_plan = self._get_response_plan_or_log(response_plan_idx)
        if response_plan is None:
            return

        self._mark_actions_executing(response_plan_idx, pending_actions)

        final_state = await self._resume_graph_or_mark_failed(
            response_plan=response_plan,
            response_plan_idx=response_plan_idx,
            pending_actions=pending_actions,
        )
        if final_state is None:
            return

        final_status = self._apply_final_outcome(
            response_plan_idx=response_plan_idx,
            pending_actions=pending_actions,
            final_state=final_state,
        )
        self._resolve_incident_on_success(response_plan_idx, final_status)

    def _mark_plan_executed_without_actions(self, response_plan_idx: int) -> None:
        self.response_plan_service.update_status(
            response_plan_idx, ResponsePlanStatus.EXECUTED.value
        )
        self.incident_service.mark_resolved_for_executed_response_plan(
            response_plan_idx
        )

    async def _resume_graph_or_mark_failed(
        self,
        response_plan: ResponsePlan,
        response_plan_idx: int,
        pending_actions: list[int],
    ) -> ResponsePlanState | None:
        try:
            return await self._resume_response_plan_graph(response_plan)
        except Exception as exc:
            logger.exception(
                "Response plan agent thread resumption failed - response_plan_idx=%s: %s",
                response_plan_idx,
                exc,
            )
            self._mark_actions_failed_after_resume_error(
                response_plan_idx=response_plan_idx,
                pending_actions=pending_actions,
                exc=exc,
            )
            return None

    def _apply_final_outcome(
        self,
        response_plan_idx: int,
        pending_actions: list[int],
        final_state: ResponsePlanState,
    ) -> str:
        tool_results = self._extract_tool_results(final_state)
        failed = self._apply_tool_results_to_actions(pending_actions, tool_results)
        final_summary = self._extract_final_summary(final_state)
        return self._update_final_plan_status_and_execution_result(
            response_plan_idx=response_plan_idx,
            final_summary=final_summary,
            failed=failed,
        )

    def _get_response_plan_or_log(
        self, response_plan_idx: int
    ) -> ResponsePlan | None:
        response_plan = self.response_plan_service.get_by_idx(response_plan_idx)
        if response_plan is None:
            logger.error(
                "Response plan not found - response_plan_idx=%s", response_plan_idx
            )
        return response_plan

    def _mark_actions_executing(
        self, response_plan_idx: int, pending_actions: list[int]
    ) -> None:
        self.response_plan_service.update_status(
            response_plan_idx, ResponsePlanStatus.EXECUTING.value
        )

        for action_idx in pending_actions:
            self.action_service.update_status(
                action_idx,
                ResponsePlanActionStatus.EXECUTING.value,
            )

    async def _resume_response_plan_graph(
        self, response_plan: ResponsePlan
    ) -> ResponsePlanState:
        await self.response_plan_agent.initialize()
        if self.response_plan_agent.graph is None:
            raise RuntimeError("Response plan agent graph is not initialized")

        config = cast(
            RunnableConfig, {"configurable": {"thread_id": response_plan.thread_id}}
        )

        return cast(
            ResponsePlanState,
            await self.response_plan_agent.graph.ainvoke(None, config=config),
        )

    def _mark_actions_failed_after_resume_error(
        self,
        response_plan_idx: int,
        pending_actions: list[int],
        exc: Exception,
    ) -> None:
        self.response_plan_service.update_status(
            response_plan_idx, ResponsePlanStatus.FAILED.value
        )
        for action_idx in pending_actions:
            self.action_service.update_status(
                action_idx,
                ResponsePlanActionStatus.FAILED.value,
                {"ok": False, "error": f"Agent resumption failed: {str(exc)}"},
            )

    def _extract_tool_results(
        self, final_state: ResponsePlanState
    ) -> dict[str, str]:
        messages = final_state.get("messages", [])
        tool_results: dict[str, str] = {}
        for message in messages:
            if isinstance(message, ToolMessage) and message.name:
                tool_results[message.name] = str(message.content)
        return tool_results

    def _apply_tool_results_to_actions(
        self, pending_actions: list[int], tool_results: dict[str, str]
    ) -> bool:
        failed = False
        for action_idx in pending_actions:
            action = self.action_service.get_by_idx(action_idx)
            if action is None:
                continue

            if action.tool_name in tool_results:
                result_content = tool_results[action.tool_name]
                self.action_service.update_status(
                    action_idx,
                    ResponsePlanActionStatus.EXECUTED.value,
                    self._parse_json_tool_result(result_content),
                )
            else:
                failed = True
                self.action_service.update_status(
                    action_idx,
                    ResponsePlanActionStatus.FAILED.value,
                    {
                        "ok": False,
                        "error": f"Tool execution result not found in agent thread for: {action.tool_name}",
                    },
                )
        return failed

    def _parse_json_tool_result(self, result_content: str) -> dict[str, object]:
        try:
            parsed_result = json.loads(result_content)
        except Exception:
            parsed_result = {"output": str(result_content)}
        return cast(dict[str, object], parsed_result)

    def _extract_final_summary(self, final_state: ResponsePlanState) -> str:
        final_summary = final_state.get("response_plan_summary")
        if final_summary:
            return extract_text_from_content(final_summary)

        messages = final_state.get("messages", [])
        if messages:
            return extract_text_from_content(messages[-1].content)
        return "대응 조치를 성공적으로 완료했습니다."

    def _update_final_plan_status_and_execution_result(
        self,
        response_plan_idx: int,
        final_summary: str,
        failed: bool,
    ) -> str:
        final_status = (
            ResponsePlanStatus.FAILED.value
            if failed
            else ResponsePlanStatus.EXECUTED.value
        )
        with self.response_plan_service.session_factory() as db:
            db_plan = (
                db.query(ResponsePlan)
                .filter(ResponsePlan.idx == response_plan_idx)
                .first()
            )
            if db_plan:
                db_plan.execution_result = final_summary
                db_plan.status = final_status
                db.commit()
        return final_status

    def _resolve_incident_on_success(
        self, response_plan_idx: int, final_status: str
    ) -> None:
        if final_status == ResponsePlanStatus.EXECUTED.value:
            self.incident_service.mark_resolved_for_executed_response_plan(
                response_plan_idx
            )
