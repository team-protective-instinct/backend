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

# settings.db_url을 psycopg 호환 URI로 조정 (+어댑터 제거)
db_uri = settings.db_url.replace("+psycopg2", "").replace("+asyncpg", "")

connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": 0,
}

pool = ConnectionPool(conninfo=db_uri, kwargs=connection_kwargs)
postgres_checkpointer = PostgresSaver(pool)  # type: ignore
postgres_checkpointer.setup()  # 최초 실행 시 체크포인트 테이블 자동 생성

threat_agent_graph = workflow.compile(checkpointer=postgres_checkpointer)
