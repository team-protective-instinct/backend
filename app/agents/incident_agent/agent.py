import asyncio
from contextlib import AbstractAsyncContextManager
from typing import cast

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode

from app.core.config import Settings

from .constants import AnalyzerNodeName
from .nodes import generate_final_report, reason_and_act, should_continue
from .state import AgentState
from .tools import ElasticsearchMCPToolProvider


class IncidentAgent:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._tools: list[BaseTool] = []
        self.mcp_tools = ElasticsearchMCPToolProvider(settings)
        self._initialize_lock = asyncio.Lock()
        self._initialized = False
        self.graph: CompiledStateGraph | None = None
        self._checkpointer_cm: (
            AbstractAsyncContextManager[AsyncPostgresSaver] | None
        ) = None
        self._checkpointer: AsyncPostgresSaver | None = None

    async def initialize(self) -> None:
        if self._initialized:
            return
        async with self._initialize_lock:
            if self._initialized:
                return
            await self.mcp_tools.initialize()
            self._tools = self.mcp_tools.tools
            await self._open_checkpointer()
            try:
                self.graph = self._build_graph()
            except Exception:
                await self._close_checkpointer()
                raise
            self._initialized = True

    def _build_graph(self) -> CompiledStateGraph:
        """에이전트 그래프를 생성하고 컴파일합니다."""
        tools = self._tools

        async def agent_node(state: object):
            return await reason_and_act(cast(AgentState, state), tools)

        async def report_node(state: object):
            return await generate_final_report(cast(AgentState, state), tools)

        workflow = StateGraph(AgentState)
        workflow.add_node(AnalyzerNodeName.AGENT, agent_node)
        workflow.add_node(AnalyzerNodeName.TOOLS, ToolNode(tools))
        workflow.add_node(AnalyzerNodeName.GENERATE_REPORT, report_node)

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

        if self._checkpointer is None:
            raise RuntimeError("IncidentAgent checkpointer was not initialized")

        return workflow.compile(checkpointer=self._checkpointer)

    async def _open_checkpointer(self) -> None:
        if self._checkpointer is not None:
            return
        self._checkpointer_cm = AsyncPostgresSaver.from_conn_string(
            self.settings.db_url
        )
        self._checkpointer = await self._checkpointer_cm.__aenter__()
        await self._checkpointer.setup()

    async def _close_checkpointer(self) -> None:
        if self._checkpointer_cm is not None:
            await self._checkpointer_cm.__aexit__(None, None, None)
        self._checkpointer_cm = None
        self._checkpointer = None

    async def ainvoke(self, input_data: AgentState, config: RunnableConfig):
        await self.initialize()
        if self.graph is None:
            raise RuntimeError("IncidentAgent graph was not initialized")
        return await self.graph.ainvoke(input_data, config=config)

    async def aclose(self) -> None:
        await self._close_checkpointer()
