from collections.abc import Sequence

from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.tools import BaseTool
from langgraph.graph import END

from app.core.llm import get_llm
from .prompt import RESPONSE_PLAN_AGENT_SYSTEM_PROMPT
from .state import ResponsePlanState
from app.agents.utils import extract_text_from_content


async def agent_node(state: ResponsePlanState, tools: Sequence[BaseTool]):
    """
    Node for the LLM to decide the next action based on messages.
    """
    llm = get_llm(temperature=0.3)
    llm_with_tools = llm.bind_tools(list(tools))

    system_prompt = SystemMessage(content=RESPONSE_PLAN_AGENT_SYSTEM_PROMPT)
    messages = [system_prompt] + state["messages"]

    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response]}


async def summarize_node(state: ResponsePlanState):
    """
    Node to generate the final execution summary using the LLM.
    """
    llm = get_llm(temperature=0.3)

    system_prompt = SystemMessage(
        content=(
            "You are a senior cyber incident response planner.\n\n"
            "Always answer in Korean.\n\n"
            "The defense actions have been executed. Please review the execution outcomes (ToolMessages) "
            "and write a final summary and response guidance in Korean. "
            "Describe what actions succeeded, what failed, and provide follow-up recommendations for the SOC operator. "
            "Write the summary clearly using Markdown format."
        )
    )
    messages = [system_prompt] + state["messages"]
    response = await llm.ainvoke(messages)

    return {
        "messages": [response],
        "response_plan_summary": extract_text_from_content(response.content),
    }


def should_continue(state: ResponsePlanState) -> str:
    """
    Determine the next node based on presence of tool calls in the last message.
    """
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return END
