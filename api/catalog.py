"""In-process access to the tools registered on the FastMCP server.

The chat UI lists and runs tools through this catalog. It does not spawn a
stdio child. The LangGraph backend still talks to a child process so the
agent path exercises the same transport as ``run_client.py``.
"""

import asyncio
from dataclasses import dataclass
from typing import Any

from mcp.server.fastmcp.exceptions import ToolError

from api.results import stringify_tool_result
from server import main as server_main


class ToolNotFoundError(Exception):
    """Raised when a caller names a tool the server did not register."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(name)


class ToolExecutionError(Exception):
    """Raised when a registered tool rejects its arguments or crashes."""


@dataclass(frozen=True)
class ToolInfo:
    """Name and description shown in the browser tool list."""

    name: str
    description: str


class ToolCatalog:
    """Cached view of ``server.main`` tools."""

    def __init__(self) -> None:
        self._tools: list[ToolInfo] | None = None
        self._lock = asyncio.Lock()

    async def list_tools(self) -> list[ToolInfo]:
        """Return every registered tool, fetching from FastMCP once."""
        async with self._lock:
            if self._tools is None:
                raw = await server_main.mcp.list_tools()
                self._tools = [
                    ToolInfo(name=tool.name, description=tool.description or "")
                    for tool in raw
                ]
            return list(self._tools)

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """Run one tool and return its text. Unknown names raise."""
        known = {tool.name for tool in await self.list_tools()}
        if name not in known:
            raise ToolNotFoundError(name)
        try:
            raw = await server_main.mcp.call_tool(name, arguments)
        except ToolError as exc:
            message = str(exc)
            if message.lower().startswith("unknown tool"):
                raise ToolNotFoundError(name) from exc
            raise ToolExecutionError(message) from exc
        except Exception as exc:
            raise ToolExecutionError(str(exc)) from exc
        return stringify_tool_result(raw)
