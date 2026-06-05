import asyncio
import logging
from collections.abc import Sequence
from importlib import import_module
from typing import cast

from langchain_core.tools import BaseTool

from app.core.config import Settings

logger = logging.getLogger(__name__)


class VictimMCPToolProvider:
    """Loads Victim MCP tools and exposes discovered executable tools."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._lock = asyncio.Lock()
        self._initialized = False
        self._tools: list[BaseTool] = []

    @property
    def tools(self) -> list[BaseTool]:
        return list(self._tools)

    async def initialize(self) -> None:
        if self._initialized:
            return
        async with self._lock:
            if self._initialized:
                return

            try:
                loaded_tools = await self._load_tools()
            except Exception as exc:
                logger.warning(
                    "Victim MCP tools unavailable; continuing without victim context: %s",
                    exc,
                )
                self._tools = []
                self._initialized = True
                return

            loaded_tool_names = [tool.name for tool in loaded_tools]
            if not loaded_tools:
                logger.warning(
                    "No Victim MCP tools discovered; loaded tools=%s",
                    loaded_tool_names,
                )
                self._tools = []
                self._initialized = True
                return

            self._tools = list(loaded_tools)
            self._initialized = True
            logger.info(
                "Victim MCP response-plan execution enabled with tools=%s",
                [tool.name for tool in loaded_tools],
            )

    async def _load_tools(self) -> Sequence[BaseTool]:
        client_module = import_module("langchain_mcp_adapters.client")
        client_class = getattr(client_module, "MultiServerMCPClient")
        client = client_class(
            {
                "victim": {
                    "transport": "http",
                    "url": self.settings.VICTIM_MCP_URL,
                }
            }
        )
        return cast(
            Sequence[BaseTool],
            await asyncio.wait_for(
                client.get_tools(),
                timeout=self.settings.VICTIM_MCP_REQUEST_TIMEOUT_SECONDS,
            ),
        )
