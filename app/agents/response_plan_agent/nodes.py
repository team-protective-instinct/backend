import json
from functools import lru_cache
from collections.abc import Sequence
from typing import cast

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import BaseTool

from app.core.llm import get_llm
from app.schemas import ResponsePlanDraft

from .prompt import GENERATE_RESPONSE_PLAN_REQUEST, RESPONSE_PLAN_AGENT_SYSTEM_PROMPT
from .state import ResponsePlanState


@lru_cache(maxsize=1)
def _get_llm_resources():
    llm = get_llm(temperature=0.3)
    return {"response_plan_llm": llm.with_structured_output(ResponsePlanDraft)}


async def collect_victim_mcp_context(
    state: ResponsePlanState,
    tools: Sequence[BaseTool],
) -> dict[str, str]:
    list_tool = _find_tool(tools, "victim_mcp_list_uploaded_files")
    if list_tool is None:
        return {
            "victim_mcp_context": "Victim MCP context unavailable: tool disabled or not initialized."
        }

    try:
        result = await list_tool.ainvoke({})
    except Exception as exc:
        return {"victim_mcp_context": f"Victim MCP context unavailable: {exc}"}
    return {"victim_mcp_context": str(result)}


async def generate_response_plan(state: ResponsePlanState):
    resources = _get_llm_resources()
    user_prompt = HumanMessage(
        content=(
            f"{GENERATE_RESPONSE_PLAN_REQUEST}\n\n"
            "[Incident Context]\n"
            f"{json.dumps(state['context'], ensure_ascii=False, indent=2)}\n\n"
            "[Victim MCP Context]\n"
            f"{state.get('victim_mcp_context', 'Victim MCP context unavailable.')}\n\n"
            "[Retrieved Playbook Chunks]\n"
            f"{json.dumps(state['retrieved_chunks'], ensure_ascii=False, indent=2)}"
        )
    )
    draft = cast(
        ResponsePlanDraft,
        await resources["response_plan_llm"].ainvoke(
            [SystemMessage(content=RESPONSE_PLAN_AGENT_SYSTEM_PROMPT), user_prompt]
        ),
    )
    return {"response_plan": draft}


def _find_tool(tools: Sequence[BaseTool], tool_name: str) -> BaseTool | None:
    for candidate in tools:
        if candidate.name == tool_name:
            return candidate
    return None
