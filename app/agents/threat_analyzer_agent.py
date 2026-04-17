import json
import uuid
from typing import Annotated, TypedDict, Optional

from app.core.config import settings
from app.core.database import SessionLocal
from app.schemas import FinalSecurityAnalysis, IncidentReport
from app.services import create_incident_from_analysis
from .prompt import (
    THREAT_ANALYSIS_AGENT_SYSTEM_PROMPT,
    VERDICT_SYSTEM_PROMPT,
    INCIDENT_REPORT_SYSTEM_PROMPT,
)

# LangChain 및 LangGraph 관련 라이브러리
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    # 구조화된 데이터를 명시적으로 저장할 필드 추가
    final_analysis: Optional[FinalSecurityAnalysis]
    incident_report: Optional[IncidentReport]


@tool
def check_ip_reputation(ip_address: str) -> str:
    """IP 주소의 악성 여부 및 위협 인텔리전스 정보를 확인합니다."""
    print(f"  [Tool 실행] IP 평판 조회 중... ({ip_address})")

    malicious_ips = ["103.22.1.5", "45.33.22.11"]
    internal_ips = ["192.168.1.100", "10.0.0.5"]

    if ip_address in malicious_ips:
        return f"경고: {ip_address}는 과거 웹 해킹 이력이 있는 악성 IP로 분류되어 있습니다."
    elif ip_address in internal_ips:
        return f"안전: {ip_address}는 내부망 IP입니다."
    return f"중립: {ip_address}에 대한 특별한 위협 정보가 없습니다."


@tool
def analyze_payload(payload: str) -> str:
    """HTTP 요청 페이로드(URI, Body 등)를 분석하여 공격 시그니처를 확인합니다."""
    print(f"  [Tool 실행] 페이로드 분석 중... ({payload})")

    payload_upper = payload.upper()
    if "UNION SELECT" in payload_upper or "OR 1=1" in payload_upper:
        return "위험: 명백한 SQL Injection 시그니처가 탐지되었습니다."
    elif "<SCRIPT>" in payload_upper or "ONERROR=" in payload_upper:
        return "위험: XSS (Cross-Site Scripting) 공격 시그니처가 탐지되었습니다."

    return "안전: 알려진 공격 시그니처가 발견되지 않았습니다. 정상적인 요청일 가능성이 높습니다."


tools = [check_ip_reputation, analyze_payload]


llm = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    google_api_key=settings.GOOGLE_API_KEY,
    temperature=0.7,
)

# 도구 사용을 위한 바인딩
llm_with_tools = llm.bind_tools(tools)

# 구조화된 출력을 위한 바인딩
llm_verdict = llm.with_structured_output(FinalSecurityAnalysis)
llm_report = llm.with_structured_output(IncidentReport)


def reason_and_act(state: AgentState):
    """
    LLM이 메시지를 보고 다음 행동(도구 호출 또는 분석 종료)을 결정하는 노드.
    """
    system_prompt = SystemMessage(content=THREAT_ANALYSIS_AGENT_SYSTEM_PROMPT)

    messages = [system_prompt] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def finalize_verdict(state: AgentState):
    """
    지금까지의 분석 내용을 바탕으로 FinalSecurityAnalysis 스키마에 맞는 정오탐 판결을 내립니다.
    """
    verdict_prompt = SystemMessage(content=VERDICT_SYSTEM_PROMPT)

    messages = [verdict_prompt] + state["messages"]
    verdict = llm_verdict.invoke(messages)

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

    messages = (
        [report_prompt] + state["messages"] + [state["final_analysis"]]
    )  # 판결 결과를 메시지에 포함
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


workflow = StateGraph(AgentState)
workflow.add_node("agent", reason_and_act)
workflow.add_node("tools", ToolNode(tools))
workflow.add_node("finalize", finalize_verdict)
workflow.add_node("generate_report", generate_incident_report)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges(
    "agent", should_continue, {"tools": "tools", "finalize": "finalize"}
)
workflow.add_edge("tools", "agent")
workflow.add_edge("finalize", "generate_report")
workflow.add_edge("generate_report", END)

# settings.db_url을 psycopg 호환 URI로 조정 (+어댑터 제거)
db_uri = settings.db_url.replace("+psycopg2", "").replace("+asyncpg", "")

connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": 0,
}

pool = ConnectionPool(
    conninfo=db_uri,
    kwargs=connection_kwargs
)
# Pylance/Pyright에서 ConnectionPool 제네릭 타입 때문에 뜨는 에러는 무시
postgres_checkpointer = PostgresSaver(pool) # type: ignore
postgres_checkpointer.setup() # 최초 실행 시 체크포인트 테이블 자동 생성

threat_agent_graph = workflow.compile(checkpointer=postgres_checkpointer)


def run_threat_analysis(log_text: str):
    """
    위협 분석 실행 및 결과(State) 반환.
    실행 완료 후, 해당 결과를 thread_id와 함께 데이터베이스에 자동으로 기록합니다.
    """
    thread_id = str(uuid.uuid4())
    
    initial_state: AgentState = {
        "messages": [
            HumanMessage(
                content=f"다음 로그를 분석하여 정오탐을 판별해주세요:\n{log_text}"
            )
        ],
        "final_analysis": None,
        "incident_report": None,
    }

    print("\n" + "=" * 50)
    print(f"🚨 [위협 분석 시작 - Thread ID: {thread_id}]")

    # stream 대신 invoke를 사용하여 최종 state를 직접 받아옵니다.
    # (중간 과정을 보고 싶다면 stream을 쓰되 state를 누적 관리해야 함)
    final_state = threat_agent_graph.invoke(
        initial_state, 
        config={"configurable": {"thread_id": thread_id}}
    )

    verdict_dict = None
    report_dict = None
    is_threat = False

    if final_state.get("final_analysis"):
        analysis = final_state["final_analysis"]
        verdict_dict = analysis.model_dump()
        is_threat = analysis.is_true_positive
        
        print("💡 [1단계: 최종 판결 완료]")
        print(
            f"   - 판결: {'정탐 (True Positive)' if is_threat else '오탐 (False Positive)'}"
        )
        print(f"   - 신뢰도: {analysis.confidence_score}")
        print(f"   - 요약: {analysis.executive_summary}")

    if final_state.get("incident_report"):
        report = final_state["incident_report"]
        report_dict = report.model_dump()
        
        print("📝 [2단계: 사건 보고서 발행 완료]")
        print(
            json.dumps(
                report_dict,
                ensure_ascii=False,
                indent=2,
            )
        )

    print("=" * 50 + "\n")
    print("⏳ 데이터베이스에 분석 결과를 저장하는 중...")
    
    db = SessionLocal()
    try:
        create_incident_from_analysis(
            db=db,
            title=f"자동 로그 분석 - {thread_id[:8]}",
            raw_log=log_text,
            verdict_data=verdict_dict,
            report_data=report_dict,
            is_threat=is_threat,
            thread_id=thread_id
        )
        print(f"✅ DB 저장 완료 (Thread ID: {thread_id})")
    except Exception as e:
        print(f"❌ DB 저장 오류: {e}")
    finally:
        db.close()

    # Controller 등 외부에서 사용할 수 있도록 thread_id도 함께 반환
    final_state["thread_id"] = thread_id
    
    return final_state


if __name__ == "__main__":
    suspicious_log_1 = """
    [Access Log]
    Time: 2026-04-14 10:23:45
    IP: 103.22.1.5
    Method: GET
    URI: /login.php?user=admin' OR 1=1 --
    User-Agent: Mozilla/5.0
    """

    run_threat_analysis(suspicious_log_1)
