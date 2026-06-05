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

from .constants import ResponsePlanNodeName
from .nodes import agent_node, should_continue, summarize_node
from .state import ResponsePlanState
from .tools import VictimMCPToolProvider


class ResponsePlanAgent:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.mcp_tools = VictimMCPToolProvider(settings)
        self._tools: list[BaseTool] = []
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
        tools = self._tools

        async def run_agent_node(state: object):
            return await agent_node(cast(ResponsePlanState, state), tools)

        async def run_summarize_node(state: object):
            return await summarize_node(cast(ResponsePlanState, state))

        def route_after_agent(state: object) -> str:
            return should_continue(cast(ResponsePlanState, state))

        workflow = StateGraph(ResponsePlanState)
        workflow.add_node(ResponsePlanNodeName.AGENT, run_agent_node)
        workflow.add_node(ResponsePlanNodeName.TOOLS, ToolNode(tools))
        workflow.add_node(ResponsePlanNodeName.SUMMARIZE, run_summarize_node)

        workflow.add_edge(START, ResponsePlanNodeName.AGENT)
        workflow.add_conditional_edges(
            ResponsePlanNodeName.AGENT,
            route_after_agent,
            {
                "tools": ResponsePlanNodeName.TOOLS,
                END: END,
            },
        )
        workflow.add_edge(ResponsePlanNodeName.TOOLS, ResponsePlanNodeName.SUMMARIZE)
        workflow.add_edge(ResponsePlanNodeName.SUMMARIZE, END)

        if self._checkpointer is None:
            raise RuntimeError("ResponsePlanAgent checkpointer was not initialized")

        # Compile graph with interrupt before tools
        return workflow.compile(
            interrupt_before=[ResponsePlanNodeName.TOOLS],
            checkpointer=self._checkpointer,
        )

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

    async def ainvoke(self, input_data: ResponsePlanState, config: RunnableConfig):
        await self.initialize()
        if self.graph is None:
            raise RuntimeError("ResponsePlanAgent graph was not initialized")
        return await self.graph.ainvoke(input_data, config=config)

    async def aclose(self) -> None:
        await self._close_checkpointer()
