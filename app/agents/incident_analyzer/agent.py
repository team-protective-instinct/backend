from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from psycopg_pool import ConnectionPool

from .constants import AnalyzerNodeName

from .nodes import (
    generate_final_report,
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
        workflow.add_node(AnalyzerNodeName.AGENT, reason_and_act)
        workflow.add_node(AnalyzerNodeName.TOOLS, ToolNode(tools))
        workflow.add_node(AnalyzerNodeName.GENERATE_REPORT, generate_final_report)

        workflow.add_edge(START, AnalyzerNodeName.AGENT)
        workflow.add_conditional_edges(
            AnalyzerNodeName.AGENT,
            should_continue,
            {
                AnalyzerNodeName.TOOLS: AnalyzerNodeName.TOOLS,
                AnalyzerNodeName.GENERATE_REPORT: AnalyzerNodeName.GENERATE_REPORT,
            },
        )
        workflow.add_edge(AnalyzerNodeName.TOOLS, AnalyzerNodeName.AGENT)
        workflow.add_edge(AnalyzerNodeName.GENERATE_REPORT, END)

        # Postgres 체크포인터 설정
        postgres_checkpointer = PostgresSaver(self.db_pool)  # type: ignore
        postgres_checkpointer.setup()

        return workflow.compile(checkpointer=postgres_checkpointer)

    def invoke(self, input_data: dict, config: dict):
        return self.graph.invoke(input_data, config=config)
