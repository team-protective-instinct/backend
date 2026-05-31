from typing import NotRequired, TypedDict

from app.schemas import ResponsePlanGenerationResult


class ResponsePlanState(TypedDict):
    context: dict[str, object]
    retrieved_chunks: list[dict[str, object]]
    response_plan: NotRequired[ResponsePlanGenerationResult]
