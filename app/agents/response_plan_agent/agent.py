import asyncio
from contextlib import AbstractAsyncContextManager
from typing import cast

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.core.config import Settings

from .constants import ResponsePlanNodeName
from .nodes import collect_victim_mcp_context, generate_response_plan
from .state import ResponsePlanState
from .tools import VictimMCPToolProvider


class ResponsePlanAgent:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._tools: list[BaseTool] = []
        self.mcp_tools = VictimMCPToolProvider(settings)
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

        async def victim_context_node(state: object):
            return await collect_victim_mcp_context(cast(ResponsePlanState, state), tools)

        async def generate_plan_node(state: object):
            return await generate_response_plan(cast(ResponsePlanState, state))

        workflow = StateGraph(ResponsePlanState)
        workflow.add_node(ResponsePlanNodeName.COLLECT_VICTIM_CONTEXT, victim_context_node)
        workflow.add_node(ResponsePlanNodeName.GENERATE_PLAN, generate_plan_node)
        workflow.add_edge(START, ResponsePlanNodeName.COLLECT_VICTIM_CONTEXT)
        workflow.add_edge(
            ResponsePlanNodeName.COLLECT_VICTIM_CONTEXT,
            ResponsePlanNodeName.GENERATE_PLAN,
        )
        workflow.add_edge(ResponsePlanNodeName.GENERATE_PLAN, END)

        if self._checkpointer is None:
            raise RuntimeError("ResponsePlanAgent checkpointer was not initialized")

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

    async def ainvoke(self, input_data: ResponsePlanState, config: RunnableConfig):
        await self.initialize()
        if self.graph is None:
            raise RuntimeError("ResponsePlanAgent graph was not initialized")
        return await self.graph.ainvoke(input_data, config=config)

    async def aclose(self) -> None:
        await self._close_checkpointer()
