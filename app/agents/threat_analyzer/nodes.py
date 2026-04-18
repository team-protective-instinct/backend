import json
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, merge_message_runs
from .prompt import (
    INCIDENT_REPORT_SYSTEM_PROMPT,
    THREAT_ANALYSIS_AGENT_SYSTEM_PROMPT,
    VERDICT_SYSTEM_PROMPT,
)
from .state import AgentState
from .tools import analyze_payload, check_ip_reputation
from app.core.llm import get_llm
from app.schemas.agent_schema import FinalSecurityAnalysis, IncidentReport

llm = get_llm(temperature=1.0)

# 도구 사용을 위한 바인딩
tools = [check_ip_reputation, analyze_payload]
llm_with_tools = llm.bind_tools(tools)

# 구조화된 출력을 위한 바인딩
llm_verdict = llm.with_structured_output(FinalSecurityAnalysis)
llm_report = llm.with_structured_output(IncidentReport)


def reason_and_act(state: AgentState):
    """
    LLM이 메시지를 보고 다음 행동(도구 호출 또는 분석 종료)을 결정하는 노드.
    Anthropic 모델의 엄격한 메시지 순서를 위해 연속된 메시지를 병합합니다.
    """
    system_prompt = SystemMessage(content=THREAT_ANALYSIS_AGENT_SYSTEM_PROMPT)

    # 시스템 프롬프트를 포함한 전체 메시지 구성 후, 연속된 동일 역할 메시지 병합
    messages = merge_message_runs([system_prompt] + state["messages"])
    
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def finalize_verdict(state: AgentState):
    """
    지금까지의 분석 내용을 바탕으로 FinalSecurityAnalysis 스키마에 맞는 정오탐 판결을 내립니다.
    """
    verdict_prompt = SystemMessage(content=VERDICT_SYSTEM_PROMPT)

    # Anthropic 규칙: 대화는 반드시 User 메시지로 끝나야 함
    # 마지막 AI의 분석 내용 뒤에 명시적인 요청(HumanMessage)을 추가합니다.
    nudge_msg = HumanMessage(content="위 분석 내용을 바탕으로 정해진 형식에 맞춰 최종 판결을 내려주세요.")
    
    messages = merge_message_runs([verdict_prompt] + state["messages"] + [nudge_msg])
    verdict: FinalSecurityAnalysis = llm_verdict.invoke(messages)

    print("\n[AI 분석 결과 JSON]")
    print(json.dumps(verdict.model_dump(), ensure_ascii=False, indent=2))

    # 구조화된 결과를 state에 저장하고, 기록을 위해 AIMessage도 추가
    return {
        "final_analysis": verdict,
        "messages": [
            AIMessage(content=f"[최종 판결 완료] {verdict.executive_summary}")
        ],
    }


def generate_incident_report(state: AgentState):
    """
    판결 내용을 바탕으로 최종 사건 보고서를 생성합니다.
    """
    report_prompt = SystemMessage(content=INCIDENT_REPORT_SYSTEM_PROMPT)

    # 판결 결과를 텍스트 메시지로 변환하여 포함
    analysis_result_msg = HumanMessage(
        content=f"최종 판결 내용: {json.dumps(state['final_analysis'].model_dump(), ensure_ascii=False)}"
    )
    
    # 마지막에 보고서 생성을 요청하는 넛지 추가 (Anthropic 순서 규칙 준수)
    nudge_msg = HumanMessage(content="판결 및 분석 내용을 요약하여 최종 사건 보고서를 작성해주세요.")

    messages = merge_message_runs(
        [report_prompt] + state["messages"] + [analysis_result_msg] + [nudge_msg]
    )
    report = llm_report.invoke(messages)

    return {
        "incident_report": report,
        "messages": [AIMessage(content="[사건 보고서 생성 완료]")],
    }


def should_continue(state: AgentState):
    """
    도구 호출 여부에 따라 다음 단계 결정
    """
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return "finalize"
