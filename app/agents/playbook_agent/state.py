from typing import NotRequired, TypedDict

from app.schemas import ResponsePlanDraft


class PlaybookState(TypedDict):
    context: dict[str, object]
    retrieved_chunks: list[dict[str, object]]
    response_plan: NotRequired[ResponsePlanDraft]
