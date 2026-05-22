from datetime import datetime

from pydantic import BaseModel, Field

from app.models.response_plan_model import ResponsePlan


class ResponsePlanDraft(BaseModel):
    summary: str = Field(description="Concise response plan summary")
    rationale: str = Field(description="Evidence and knowledge-base rationale")
    plan_text: str = Field(description="Detailed response procedure for the incident")


class ResponsePlanResponse(BaseModel):
    idx: int
    incident_idx: int
    thread_id: str | None
    summary: str
    rationale: str | None
    plan_text: str
    status: str
    approved_at: datetime | None
    denied_at: datetime | None
    denied_reason: str | None
    created_at: datetime
    modified_at: datetime

    @classmethod
    def from_response_plan(cls, response_plan: ResponsePlan) -> "ResponsePlanResponse":
        return cls(
            idx=response_plan.idx,
            incident_idx=response_plan.incident_idx,
            thread_id=response_plan.thread_id,
            summary=response_plan.summary,
            rationale=response_plan.rationale,
            plan_text=response_plan.plan_text,
            status=response_plan.status,
            approved_at=response_plan.approved_at,
            denied_at=response_plan.denied_at,
            denied_reason=response_plan.denied_reason,
            created_at=response_plan.created_at,
            modified_at=response_plan.modified_at,
        )


class ResponsePlanDenyRequest(BaseModel):
    denied_reason: str = Field(min_length=1, description="Reason for denying the plan")
