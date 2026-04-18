import json
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, merge_message_runs
from .prompt import (
    INCIDENT_REPORT_SYSTEM_PROMPT,
    THREAT_ANALYSIS_AGENT_SYSTEM_PROMPT,
    VERDICT_SYSTEM_PROMPT,
    FINALIZE_VERDICT_NUDGE,
    GENERATE_REPORT_NUDGE,
    ANALYSIS_RESULT_PREFIX,
)
from .state import AgentState
from .tools import analyze_payload, check_ip_reputation
from app.core.llm import get_llm
from app.schemas.agent_schema import FinalSecurityAnalysis, IncidentReport

llm = get_llm(temperature=1.0)

# Binding for tools
tools = [check_ip_reputation, analyze_payload]
llm_with_tools = llm.bind_tools(tools)

# Binding for structured output
llm_verdict = llm.with_structured_output(FinalSecurityAnalysis)
llm_report = llm.with_structured_output(IncidentReport)


def reason_and_act(state: AgentState):
    """
    Node for the LLM to decide the next action based on messages.
    Merges consecutive messages for Anthropic API compliance.
    """
    system_prompt = SystemMessage(content=THREAT_ANALYSIS_AGENT_SYSTEM_PROMPT)

    messages = merge_message_runs([system_prompt] + state["messages"])
    
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def finalize_verdict(state: AgentState):
    """
    Final security verdict node based on analysis and evidence.
    """
    verdict_prompt = SystemMessage(content=VERDICT_SYSTEM_PROMPT)

    # Nudge the LLM to provide the final verdict
    nudge_msg = HumanMessage(content=FINALIZE_VERDICT_NUDGE)
    
    messages = merge_message_runs([verdict_prompt] + state["messages"] + [nudge_msg])
    verdict: FinalSecurityAnalysis = llm_verdict.invoke(messages)

    print("\n[AI Analysis Result JSON]")
    print(json.dumps(verdict.model_dump(), ensure_ascii=False, indent=2))

    # Save structured results to state and add an AIMessage for tracking
    return {
        "final_analysis": verdict,
        "messages": [
            AIMessage(content=f"[Final Verdict Completed] {verdict.executive_summary}")
        ],
    }


def generate_incident_report(state: AgentState):
    """
    Node to generate the final incident report based on the verdict.
    """
    report_prompt = SystemMessage(content=INCIDENT_REPORT_SYSTEM_PROMPT)

    # Include the verdict as a text message
    analysis_result_msg = HumanMessage(
        content=f"{ANALYSIS_RESULT_PREFIX}{json.dumps(state['final_analysis'].model_dump(), ensure_ascii=False)}"
    )
    
    # Nudge the LLM to write the report
    nudge_msg = HumanMessage(content=GENERATE_REPORT_NUDGE)

    messages = merge_message_runs(
        [report_prompt] + state["messages"] + [analysis_result_msg] + [nudge_msg]
    )
    report = llm_report.invoke(messages)

    return {
        "incident_report": report,
        "messages": [AIMessage(content="[Incident Report Generation Completed]")],
    }


def should_continue(state: AgentState):
    """
    Determine the next node based on presence of tool calls.
    """
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return "finalize"
