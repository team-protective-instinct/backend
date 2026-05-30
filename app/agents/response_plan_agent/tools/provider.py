import asyncio
import logging
from importlib import import_module
from collections.abc import Sequence
from typing import cast

from langchain_core.tools import BaseTool

from app.core.config import Settings

from .victim_mcp_tool import build_list_uploaded_files_wrapper

logger = logging.getLogger(__name__)


class VictimMCPToolProvider:
    """Loads Victim MCP tools and exposes safe response-planning wrappers."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._lock = asyncio.Lock()
        self._initialized = False
        self._tools: list[BaseTool] = []
        self._list_uploaded_files_tool: BaseTool | None = None

    @property
    def tools(self) -> list[BaseTool]:
        return list(self._tools)

    async def initialize(self) -> None:
        if self._initialized:
            return
        async with self._lock:
            if self._initialized:
                return
            if not self.settings.VICTIM_MCP_ENABLED:
                logger.info("Victim MCP disabled for response plan agent")
                self._initialized = True
                return

            try:
                loaded_tools = await self._load_tools()
            except Exception as exc:
                logger.warning(
                    "Victim MCP tools unavailable; continuing without victim context: %s",
                    exc,
                )
                self._list_uploaded_files_tool = None
                self._tools = []
                self._initialized = True
                return

            list_tool = self._find_tool(loaded_tools, "list_uploaded_files")
            if list_tool is None:
                loaded_tool_names = [tool.name for tool in loaded_tools]
                logger.warning(
                    "Victim MCP list_uploaded_files tool not found; loaded tools=%s. "
                    "Response plan agent will continue without Victim MCP context. "
                    "If capstone-victim source already registers list_uploaded_files, "
                    "rebuild/restart the DVWA victim container so the running MCP server matches the source.",
                    loaded_tool_names,
                )
                self._list_uploaded_files_tool = None
                self._tools = []
                self._initialized = True
                return

            self._list_uploaded_files_tool = list_tool
            self._tools = [build_list_uploaded_files_wrapper(self.settings, list_tool)]
            self._initialized = True
            logger.info("Victim MCP response-plan context enabled")

    async def _load_tools(self) -> Sequence[BaseTool]:
        client_module = import_module("langchain_mcp_adapters.client")
        client_class = getattr(client_module, "MultiServerMCPClient")
        client = client_class(
            {
                "victim": {
                    "transport": "http",
                    "url": self.settings.VICTIM_MCP_URL,
                }
            },
            tool_name_prefix=True,
        )
        return cast(
            Sequence[BaseTool],
            await asyncio.wait_for(
                client.get_tools(),
                timeout=self.settings.VICTIM_MCP_REQUEST_TIMEOUT_SECONDS,
            ),
        )

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
