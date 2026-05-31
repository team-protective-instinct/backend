from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.response_plan_action_model import ResponsePlanAction
from app.models.response_plan_model import ResponsePlan


class ResponsePlanActionGeneration(BaseModel):
    execution_order: int = Field(ge=1, description="Order in which to execute this action")
    tool_name: str = Field(description="Victim MCP tool name to execute")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Tool arguments")
    reason: str = Field(description="Why this action should be executed")


class ResponsePlanGenerationResult(BaseModel):
    summary: str = Field(description="Concise response plan summary")
    actions: list[ResponsePlanActionGeneration] = Field(
        default_factory=list,
        description="Victim MCP defense actions to persist and execute",
    )


ResponsePlanDraft = ResponsePlanGenerationResult


class ResponsePlanActionResponse(BaseModel):
    idx: int
    response_plan_idx: int
    execution_order: int
    tool_name: str
    arguments: dict[str, Any]
    reason: str | None
    status: str
    result: dict[str, Any] | None
    created_at: datetime
    modified_at: datetime

    @classmethod
    def from_action(cls, action: ResponsePlanAction) -> "ResponsePlanActionResponse":
        return cls(
            idx=action.idx,
            response_plan_idx=action.response_plan_idx,
            execution_order=action.execution_order,
            tool_name=action.tool_name,
            arguments=action.arguments,
            reason=action.reason,
            status=action.status,
            result=action.result,
            created_at=action.created_at,
            modified_at=action.modified_at,
        )


class ResponsePlanResponse(BaseModel):
    idx: int
    incident_idx: int
    thread_id: str | None
    summary: str
    status: str
    denied_reason: str | None
    actions: list[ResponsePlanActionResponse]
    created_at: datetime
    modified_at: datetime

    @classmethod
    def from_response_plan(cls, response_plan: ResponsePlan) -> "ResponsePlanResponse":
        return cls(
            idx=response_plan.idx,
            incident_idx=response_plan.incident_idx,
            thread_id=response_plan.thread_id,
            summary=response_plan.summary,
            status=response_plan.status,
            denied_reason=response_plan.denied_reason,
            actions=[
                ResponsePlanActionResponse.from_action(action)
                for action in response_plan.actions
            ],
            created_at=response_plan.created_at,
            modified_at=response_plan.modified_at,
        )


class ResponsePlanDenyRequest(BaseModel):
    denied_reason: str = Field(min_length=1, description="Reason for denying the plan")
