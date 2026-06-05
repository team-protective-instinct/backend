from typing import Annotated, TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class ResponsePlanState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    context: dict[str, object]
    retrieved_chunks: list[dict[str, object]]
    response_plan_summary: str | None
