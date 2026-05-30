from typing import NotRequired, TypedDict

from app.schemas import ResponsePlanDraft


class ResponsePlanState(TypedDict):
    context: dict[str, object]
    retrieved_chunks: list[dict[str, object]]
    victim_mcp_context: NotRequired[str]
    response_plan: NotRequired[ResponsePlanDraft]
