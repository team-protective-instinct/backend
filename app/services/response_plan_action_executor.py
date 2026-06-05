import logging

from langchain_core.tools import BaseTool

from app.agents.response_plan_agent.tools import (
    VictimMCPToolProvider,
    find_tool,
    invoke_victim_mcp_action,
)
from app.core.config import Settings
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
        settings: Settings,
    ):
        self.action_service = action_service
        self.response_plan_service = response_plan_service
        self.incident_service = incident_service
        self.settings = settings
        self.mcp_tools = VictimMCPToolProvider(settings)

    async def execute_pending_actions(self, response_plan_idx: int) -> None:
        pending_actions = self.action_service.get_pending_action_ids(response_plan_idx)
        if not pending_actions:
            self.response_plan_service.update_status(
                response_plan_idx, ResponsePlanStatus.EXECUTED.value
            )
            self.incident_service.mark_resolved_for_executed_response_plan(
                response_plan_idx
            )
            return

        self.response_plan_service.update_status(
            response_plan_idx, ResponsePlanStatus.EXECUTING.value
        )

        if not self.settings.VICTIM_MCP_ENABLED:
            for action_idx in pending_actions:
                self.action_service.update_status(
                    action_idx,
                    ResponsePlanActionStatus.SKIPPED.value,
                    {
                        "ok": False,
                        "status": "skipped",
                        "reason": "Victim MCP execution is disabled",
                    },
                )
            self.response_plan_service.update_status(
                response_plan_idx, ResponsePlanStatus.FAILED.value
            )
            return

        # Victim MCP server가 활성화된 경우
        await self.mcp_tools.initialize()
        tools = self.mcp_tools.tools
        failed = False

        for action_idx in pending_actions:
            action = self.action_service.update_status(
                action_idx,
                ResponsePlanActionStatus.EXECUTING.value,
            )
            tool = self._find_action_tool(tools, action.tool_name)
            if tool is None:
                failed = True
                self.action_service.update_status(
                    action_idx,
                    ResponsePlanActionStatus.FAILED.value,
                    {
                        "ok": False,
                        "error": f"Victim MCP tool not available: {action.tool_name}",
                    },
                )
                continue

            try:
                # 실제로 victim mcp를 실행하는 부분
                result = await invoke_victim_mcp_action(
                    settings=self.settings,
                    tool=tool,
                    arguments=action.arguments,
                )
            except Exception as exc:
                failed = True
                logger.warning(
                    "Response plan action failed - response_plan_idx=%s action_idx=%s tool=%s: %s",
                    response_plan_idx,
                    action_idx,
                    action.tool_name,
                    exc,
                )
                self.action_service.update_status(
                    action_idx,
                    ResponsePlanActionStatus.FAILED.value,
                    {"ok": False, "error": str(exc)},
                )
                continue

            self.action_service.update_status(
                action_idx,
                ResponsePlanActionStatus.EXECUTED.value,
                result,
            )

        final_status = (
            ResponsePlanStatus.FAILED.value
            if failed
            else ResponsePlanStatus.EXECUTED.value
        )
        self.response_plan_service.update_status(response_plan_idx, final_status)

        if final_status == ResponsePlanStatus.EXECUTED.value:
            self.incident_service.mark_resolved_for_executed_response_plan(
                response_plan_idx
            )

    def _find_action_tool(
        self, tools: list[BaseTool], tool_name: str
    ) -> BaseTool | None:
        return find_tool(tools, tool_name)
