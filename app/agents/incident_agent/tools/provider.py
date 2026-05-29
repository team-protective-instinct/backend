import asyncio
import logging
from importlib import import_module
from collections.abc import Sequence
from typing import cast

from langchain_core.tools import BaseTool

from app.core.config import Settings

from .mcp_tool import build_search_wrapper

logger = logging.getLogger(__name__)


class ElasticsearchMCPToolProvider:
    """Loads Elasticsearch MCP tools and exposes policy-limited LangChain tools."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._lock = asyncio.Lock()
        self._initialized = False
        self._tools: list[BaseTool] = []
        self._search_tool: BaseTool | None = None

    @property
    def tools(self) -> list[BaseTool]:
        return list(self._tools)

    async def initialize(self) -> None:
        if self._initialized:
            return
        async with self._lock:
            if self._initialized:
                return
            if not self.settings.ELASTICSEARCH_MCP_ENABLED:
                logger.info("Elasticsearch MCP log search disabled")
                self._initialized = True
                return

            try:
                client_module = import_module("langchain_mcp_adapters.client")
                client_class = getattr(client_module, "MultiServerMCPClient")
                client = client_class(
                    {
                        "elasticsearch": {
                            "transport": "http",
                            "url": self.settings.ELASTICSEARCH_MCP_URL,
                        }
                    },
                    tool_name_prefix=True,
                )
                loaded_tools = cast(
                    Sequence[BaseTool],
                    await asyncio.wait_for(
                        client.get_tools(),
                        timeout=self.settings.ELASTICSEARCH_MCP_REQUEST_TIMEOUT_SECONDS,
                    ),
                )
            except Exception as exc:
                logger.warning(
                    "Elasticsearch MCP tools unavailable; continuing without log search: %s",
                    exc,
                )
                return

            search_tool = self._find_tool(loaded_tools, "search")
            if search_tool is None:
                logger.warning(
                    "Elasticsearch MCP search tool not found; loaded tools=%s",
                    [tool.name for tool in loaded_tools],
                )
                return

            self._search_tool = search_tool
            self._tools = [build_search_wrapper(self.settings, search_tool)]
            self._initialized = True
            logger.info("Elasticsearch MCP log search enabled with policy wrapper")

    def _find_tool(self, tools: Sequence[BaseTool], tool_name: str) -> BaseTool | None:
        for candidate in tools:
            name = candidate.name.lower()
            if (
                name == tool_name
                or name.endswith(f"__{tool_name}")
                or name.endswith(f"_{tool_name}")
            ):
                return candidate
        return None
