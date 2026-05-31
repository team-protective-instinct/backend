import asyncio
import logging
from importlib import import_module
from collections.abc import Sequence
from typing import cast

from langchain_core.tools import BaseTool

from app.core.config import Settings

from .victim_mcp_tool import ALLOWED_VICTIM_MCP_ACTIONS

logger = logging.getLogger(__name__)


class VictimMCPToolProvider:
    """Loads Victim MCP tools and exposes safe response-planning wrappers."""

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
                self._tools = []
                self._initialized = True
                return

            action_tools = [
                tool
                for tool in loaded_tools
                if self._base_tool_name(tool.name) in ALLOWED_VICTIM_MCP_ACTIONS
            ]
            loaded_tool_names = [tool.name for tool in loaded_tools]
            missing_tools = sorted(
                ALLOWED_VICTIM_MCP_ACTIONS
                - {self._base_tool_name(tool.name) for tool in action_tools}
            )
            if missing_tools:
                logger.warning(
                    "Victim MCP defense tools missing; missing=%s loaded=%s",
                    missing_tools,
                    loaded_tool_names,
                )

            if not action_tools:
                loaded_tool_names = [tool.name for tool in loaded_tools]
                logger.warning(
                    "No executable Victim MCP defense tools found; loaded tools=%s",
                    loaded_tool_names,
                )
                self._tools = []
                self._initialized = True
                return

            self._tools = action_tools
            self._initialized = True
            logger.info(
                "Victim MCP response-plan execution enabled with tools=%s",
                [tool.name for tool in action_tools],
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

    def _base_tool_name(self, tool_name: str) -> str:
        name = tool_name.lower()
        if name.startswith("victim__"):
            return name.removeprefix("victim__")
        if name.startswith("victim_"):
            return name.removeprefix("victim_")
        return name
