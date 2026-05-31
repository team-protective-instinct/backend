import asyncio
from collections.abc import Sequence

from langchain_core.tools import BaseTool

from app.core.config import Settings

ALLOWED_VICTIM_MCP_ACTIONS = {
    "quarantine_suspicious_uploads",
    "disable_php_execution_in_uploads",
    "restart_apache",
}


async def invoke_victim_mcp_action(
    settings: Settings,
    tool: BaseTool,
    arguments: dict[str, object],
) -> dict[str, object]:
    result = await asyncio.wait_for(
        tool.ainvoke(arguments),
        timeout=settings.VICTIM_MCP_REQUEST_TIMEOUT_SECONDS,
    )
    return {
        "source": "victim_mcp",
        "tool": tool.name,
        "result": result,
    }


def find_tool(tools: Sequence[BaseTool], tool_name: str) -> BaseTool | None:
    for candidate in tools:
        name = candidate.name.lower()
        if (
            name == tool_name
            or name.endswith(f"__{tool_name}")
            or name.endswith(f"_{tool_name}")
        ):
            return candidate
    return None
