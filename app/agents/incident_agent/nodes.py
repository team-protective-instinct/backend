from typing import cast
from collections.abc import Sequence
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    merge_message_runs,
)
from langchain_core.tools import BaseTool

from .constants import AnalyzerNodeName
from .prompt import (
    ANALYSIS_REPORT_SYSTEM_PROMPT,
    THREAT_ANALYSIS_AGENT_SYSTEM_PROMPT,
    GENERATE_REPORT_NUDGE,
)
from .state import AgentState
from app.core.llm import get_llm
from app.schemas.agent_schema import AnalysisReport


AGENT_CONTEXT_PREFIX = "Incident agent context (trusted metadata):\n"


def _get_llm_resources(tools: Sequence[BaseTool]):
    """
    Lazy loader for LLM instances to avoid overhead during module import.
    """
    llm = get_llm(temperature=1.0)

    return {
        "llm_with_tools": llm.bind_tools(list(tools)),
        "llm_analysis_report": llm.with_structured_output(AnalysisReport),
    }


async def reason_and_act(state: AgentState, tools: Sequence[BaseTool]):
    """
    Node for the LLM to decide the next action based on messages.
    """
    collector = _get_llm_resources(tools)["llm_with_tools"]
    system_prompt = SystemMessage(content=THREAT_ANALYSIS_AGENT_SYSTEM_PROMPT)
    context_message = _build_context_message(state.get("context"))

    base_messages: list[BaseMessage] = [system_prompt]
    if context_message is not None:
        base_messages.append(context_message)
    messages = merge_message_runs(base_messages + state["messages"])

    response = await collector.ainvoke(messages)
    return {"messages": [response]}


def _build_context_message(context: dict[str, object] | None) -> HumanMessage | None:
    if not context:
        return None
    lines = [AGENT_CONTEXT_PREFIX]
    source = context.get("source")
    if isinstance(source, str) and source.strip():
        lines.append(f"source: {source.strip()}")
    if len(lines) == 1:
        return None
    return HumanMessage(content="\n".join(lines))


async def generate_final_report(state: AgentState, tools: Sequence[BaseTool]):
    """
    Node to generate the final integrated security analysis report.
    """
    reporter = _get_llm_resources(tools)["llm_analysis_report"]
    report_prompt = SystemMessage(content=ANALYSIS_REPORT_SYSTEM_PROMPT)

    # Nudge the LLM to provide the final integrated report
    nudge_msg = HumanMessage(content=GENERATE_REPORT_NUDGE)

    messages = merge_message_runs([report_prompt] + state["messages"] + [nudge_msg])
    report = cast(AnalysisReport, await reporter.ainvoke(messages))

    # Save structured results to state and add an AIMessage for tracking
    return {
        "analysis_result": report,
        "messages": [
            AIMessage(
                content=f"[Analysis & Reporting Completed] Verdict: {'TP' if report.is_true_positive else 'FP'}"
            )
        ],
    }


def should_continue(state: AgentState):
    """
    Determine the next node based on presence of tool calls.
    """
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return AnalyzerNodeName.TOOLS
    return AnalyzerNodeName.GENERATE_REPORT
