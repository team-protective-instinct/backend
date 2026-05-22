from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from psycopg import Connection
from psycopg.rows import DictRow
from psycopg_pool import ConnectionPool

from .constants import ResponsePlanNodeName
from .nodes import generate_response_plan
from .state import ResponsePlanState


class ResponsePlanAgent:
    def __init__(self, db_pool: ConnectionPool[Connection[DictRow]]):
        self.db_pool = db_pool
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(ResponsePlanState)
        workflow.add_node(ResponsePlanNodeName.GENERATE_PLAN, generate_response_plan)
        workflow.add_edge(START, ResponsePlanNodeName.GENERATE_PLAN)
        workflow.add_edge(ResponsePlanNodeName.GENERATE_PLAN, END)

        postgres_checkpointer = PostgresSaver(self.db_pool)
        postgres_checkpointer.setup()

        return workflow.compile(checkpointer=postgres_checkpointer)

    def invoke(self, input_data: ResponsePlanState, config: RunnableConfig):
        return self.graph.invoke(input_data, config=config)
