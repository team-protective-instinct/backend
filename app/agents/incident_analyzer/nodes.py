import json
import logging
from typing import cast
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    merge_message_runs,
)

from .constants import AnalyzerNodeName
from .prompt import (
    ANALYSIS_REPORT_SYSTEM_PROMPT,
    THREAT_ANALYSIS_AGENT_SYSTEM_PROMPT,
    GENERATE_REPORT_NUDGE,
)
from functools import lru_cache
from .state import AgentState
from .tools import analyze_payload, check_ip_reputation
from app.core.llm import get_llm
from app.schemas.agent_schema import SecurityAnalysisReport

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_llm_resources():
    """
    Lazy loader for LLM instances to avoid overhead during module import.
    """
    llm = get_llm(temperature=1.0)
    tools = [check_ip_reputation, analyze_payload]

    return {
        "llm_with_tools": llm.bind_tools(tools),
        "llm_analysis_report": llm.with_structured_output(SecurityAnalysisReport),
    }


def reason_and_act(state: AgentState):
    """
    Node for the LLM to decide the next action based on messages.
    """
    resources = _get_llm_resources()
    system_prompt = SystemMessage(content=THREAT_ANALYSIS_AGENT_SYSTEM_PROMPT)

    messages = merge_message_runs([system_prompt] + state["messages"])

    response = resources["llm_with_tools"].invoke(messages)
    return {"messages": [response]}


def generate_final_report(state: AgentState):
    """
    Node to generate the final integrated security analysis report.
    """
    resources = _get_llm_resources()
    report_prompt = SystemMessage(content=ANALYSIS_REPORT_SYSTEM_PROMPT)

    # Nudge the LLM to provide the final integrated report
    nudge_msg = HumanMessage(content=GENERATE_REPORT_NUDGE)

    messages = merge_message_runs([report_prompt] + state["messages"] + [nudge_msg])
    report = cast(
        SecurityAnalysisReport, resources["llm_analysis_report"].invoke(messages)
    )

    logger.info("AI Analysis Result JSON:")
    logger.info(json.dumps(report.model_dump(), ensure_ascii=False, indent=2))

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
