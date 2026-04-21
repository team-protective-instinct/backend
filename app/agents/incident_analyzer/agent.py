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


class ThreatAnalyzerAgent:
    def __init__(self, db_pool: ConnectionPool):
        self.db_pool = db_pool
        self.graph = self._build_graph()

    def _build_graph(self):
        """에이전트 그래프를 생성하고 컴파일합니다."""
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

        # Postgres 체크포인터 설정
        postgres_checkpointer = PostgresSaver(self.db_pool)  # type: ignore
        postgres_checkpointer.setup()
        
        return workflow.compile(checkpointer=postgres_checkpointer)

    def invoke(self, input_data: dict, config: dict):
        return self.graph.invoke(input_data, config=config)
