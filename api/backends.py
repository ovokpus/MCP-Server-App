"""Chat backends used by the HTTP API.

``LocalToolBackend`` runs the phrase router in ``api.routing`` against the
in-process tool catalog. ``OpenAIBackend`` lazily constructs the existing
``MCPLangGraphAgent``, which spawns the MCP server over stdio.

``AGENT_MODE=auto`` (the default) picks OpenAI when the key looks real and
local routing otherwise, so ``docker compose up`` works from ``.env.sample``.
"""

import asyncio
import os
from dataclasses import dataclass, field
from typing import Any, Protocol

from client.langgraph_agent import MCPLangGraphAgent

from api.catalog import ToolCatalog, ToolExecutionError, ToolInfo
from api.config import agent_mode, openai_key_is_usable, openai_model_name
from api.routing import plan_local_calls

_LOCAL_NOTE = (
    "Local mode ran the MCP tools directly, without a language model. "
    "Set a real OPENAI_API_KEY to let the LangGraph agent answer in its own words."
)

_LOCAL_HELP = (
    "This session is in local mode, so I only run tools I can recognize in the "
    "message. Try \"Roll 2d6\", \"Create a quote card about shipping\", "
    "\"Create a LinkedIn post about Python\", \"Get a slide image about robots\", "
    "\"Search the web for AI news\", or \"Search GitHub for langgraph\". "
    "Open-ended chat needs an OpenAI key."
)


class BackendNotReady(Exception):
    """Raised when a chat turn cannot run with the current configuration."""


@dataclass
class ToolTrace:
    """One tool call the UI can show under an assistant message."""

    name: str
    arguments: dict[str, Any]
    result: str


@dataclass
class ChatTurn:
    """Result of a single user message."""

    reply: str
    backend: str
    tool_calls: list[ToolTrace] = field(default_factory=list)


class AgentBackend(Protocol):
    """What the FastAPI routes need from either backend."""

    name: str

    def readiness(self) -> tuple[bool, str]:
        """Return whether chat can run, plus a sentence for the status pill."""

    async def list_tools(self) -> list[ToolInfo]:
        """Tools to show in the sidebar."""

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """Direct tool invocation from the "Run tool" panel."""

    async def chat(
        self,
        message: str,
        history: list[dict[str, str]],
        use_state_graph: bool,
    ) -> ChatTurn:
        """Answer one user message."""


class LocalToolBackend:
    """Phrase router over the in-process MCP tools."""

    name = "local"

    def __init__(self, catalog: ToolCatalog) -> None:
        self._catalog = catalog

    def readiness(self) -> tuple[bool, str]:
        return (
            True,
            "Local tool routing is active. Add a real OPENAI_API_KEY to use the LangGraph agent.",
        )

    async def list_tools(self) -> list[ToolInfo]:
        return await self._catalog.list_tools()

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        return await self._catalog.call_tool(name, arguments)

    async def chat(
        self,
        message: str,
        history: list[dict[str, str]],
        use_state_graph: bool,
    ) -> ChatTurn:
        # History and the graph switch matter for the OpenAI backend. Local
        # mode still records them on the session so the transcript stays intact.
        del history, use_state_graph
        traces: list[ToolTrace] = []
        for name, arguments in plan_local_calls(message):
            try:
                result = await self._catalog.call_tool(name, arguments)
            except ToolExecutionError as exc:
                result = f"Tool error: {exc}"
            traces.append(ToolTrace(name=name, arguments=dict(arguments), result=result))

        if not traces:
            reply = _LOCAL_HELP
        else:
            rendered = "\n\n".join(trace.result for trace in traces)
            reply = f"{rendered}\n\n{_LOCAL_NOTE}"
        return ChatTurn(reply=reply, backend=self.name, tool_calls=traces)


class OpenAIBackend:
    """LangGraph ReAct (or StateGraph) agent over the stdio MCP server."""

    name = "openai"

    def __init__(self, catalog: ToolCatalog) -> None:
        self._catalog = catalog
        self._agent: Any = None
        self._lock = asyncio.Lock()

    def readiness(self) -> tuple[bool, str]:
        if not openai_key_is_usable():
            return False, "AGENT_MODE=openai requires a real OPENAI_API_KEY."
        model = openai_model_name()
        return True, f"LangGraph agent is configured with {model}. It connects on the first message."

    async def list_tools(self) -> list[ToolInfo]:
        # The sidebar reads the same registrations the child process exposes.
        # Connecting on every health check would spawn a server process.
        return await self._catalog.list_tools()

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        return await self._catalog.call_tool(name, arguments)

    async def _ensure_agent(self) -> Any:
        """Start the stdio agent once, even if two chats arrive together."""
        async with self._lock:
            if self._agent is not None:
                return self._agent
            if not openai_key_is_usable():
                raise BackendNotReady(
                    "Set OPENAI_API_KEY to a real key, or set AGENT_MODE=local to run tools without a model."
                )
            # Construction waits for the first chat so a missing key does not
            # crash process startup. Only this call builds the OpenAI client
            # and the stdio child.
            agent = MCPLangGraphAgent(openai_api_key=os.environ["OPENAI_API_KEY"])
            try:
                await agent.initialize()
            except Exception as exc:
                raise BackendNotReady(f"Could not start the LangGraph agent: {exc}") from exc
            self._agent = agent
            return agent

    async def chat(
        self,
        message: str,
        history: list[dict[str, str]],
        use_state_graph: bool,
    ) -> ChatTurn:
        agent = await self._ensure_agent()
        try:
            detailed = await agent.chat_detailed(
                message,
                history=history,
                use_state_graph=use_state_graph,
            )
        except Exception as exc:
            raise BackendNotReady(f"The LangGraph agent failed: {exc}") from exc
        traces = [
            ToolTrace(
                name=str(item.get("name") or "tool"),
                arguments=item.get("arguments") if isinstance(item.get("arguments"), dict) else {},
                result=str(item.get("result") or ""),
            )
            for item in detailed.get("tool_calls", [])
        ]
        return ChatTurn(reply=str(detailed.get("reply") or ""), backend=self.name, tool_calls=traces)


def resolve_backend(catalog: ToolCatalog | None = None) -> LocalToolBackend | OpenAIBackend:
    """Pick a backend from ``AGENT_MODE`` and the OpenAI key."""
    tools = catalog or ToolCatalog()
    mode = agent_mode()
    if mode == "local":
        return LocalToolBackend(tools)
    if mode == "openai" or (mode == "auto" and openai_key_is_usable()):
        return OpenAIBackend(tools)
    return LocalToolBackend(tools)
