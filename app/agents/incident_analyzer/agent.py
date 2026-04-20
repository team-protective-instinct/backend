from functools import lru_cache
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from .nodes import (
    finalize_verdict,
    generate_incident_report,
    reason_and_act,
    should_continue,
)
from .state import AgentState
from .tools import analyze_payload, check_ip_reputation
from app.core.database import get_pool

@lru_cache(maxsize=1)
def get_threat_agent_graph():
    """
    팩토리 함수를 통해 에이전트 그래프를 생성합니다.
    최초 호출 시에만 컴파일 및 체크포인터 설정을 수행합니다.
    """
    tools = [check_ip_reputation, analyze_payload]
    
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

    # Postgres 체크포인터 설정 (지연 초기화)
    pool = get_pool()
    postgres_checkpointer = PostgresSaver(pool)  # type: ignore
    postgres_checkpointer.setup()
    
    return workflow.compile(checkpointer=postgres_checkpointer)

# 하위 호환성을 위해 (필요한 경우) proxy 변수나 factory 노출
# 여기서는 Lazy call을 권장하도록 함.
