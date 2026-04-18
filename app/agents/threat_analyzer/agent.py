import json
import uuid
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from psycopg_pool import ConnectionPool

from .nodes import (
    finalize_verdict,
    generate_incident_report,
    reason_and_act,
    should_continue,
)
from .state import AgentState
from .tools import analyze_payload, check_ip_reputation
from app.core.config import settings
from app.core.database import SessionLocal
from app.services.incident_service import create_incident_from_analysis

tools = [check_ip_reputation, analyze_payload]  # tools 모듈에서 가져온 도구들

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

pool = ConnectionPool(conninfo=db_uri, kwargs=connection_kwargs)
# Pylance/Pyright에서 ConnectionPool 제네릭 타입 때문에 뜨는 에러는 무시
postgres_checkpointer = PostgresSaver(pool)  # type: ignore
postgres_checkpointer.setup()  # 최초 실행 시 체크포인트 테이블 자동 생성

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
        initial_state, config={"configurable": {"thread_id": thread_id}}
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
            thread_id=thread_id,
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
