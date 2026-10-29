"""FastAPI surface for the browser chat and the direct tool runner.

The Next.js app proxies same-origin requests to these routes. A person can
also call them with curl while debugging a container.
"""

import os
import re
from typing import Any, Literal
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from api.backends import AgentBackend, BackendNotReady, resolve_backend
from api.catalog import ToolCatalog, ToolExecutionError, ToolNotFoundError
from api.config import openai_model_name
from api.sessions import SessionStore

load_dotenv()

_SESSION_ID = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


class ToolCallRequest(BaseModel):
    """Body for ``POST /api/tools/call``."""

    name: str = Field(min_length=1, max_length=80)
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolCallResponse(BaseModel):
    """Text returned by a single tool."""

    name: str
    result: str


class ToolInfoModel(BaseModel):
    """One sidebar entry."""

    name: str
    description: str


class ToolTraceModel(BaseModel):
    """A tool call attached to an assistant turn."""

    name: str
    arguments: dict[str, Any]
    result: str


class ChatMessageModel(BaseModel):
    """One stored transcript line."""

    role: Literal["user", "assistant"]
    content: str
    tool_calls: list[ToolTraceModel] = Field(default_factory=list)


class ChatRequest(BaseModel):
    """Body for ``POST /api/chat``."""

    message: str = Field(min_length=1, max_length=8000)
    session_id: str | None = None
    agent: Literal["react", "state_graph"] = "react"

    @field_validator("message")
    @classmethod
    def message_is_not_blank(cls, value: str) -> str:
        """Reject whitespace-only messages before they hit a backend."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("message must not be blank")
        return stripped


class ChatResponse(BaseModel):
    """Assistant turn plus the session id to send next time."""

    session_id: str
    reply: str
    backend: Literal["local", "openai"]
    agent: Literal["react", "state_graph"]
    tool_calls: list[ToolTraceModel]


class SessionResponse(BaseModel):
    """Full transcript for a session."""

    session_id: str
    messages: list[ChatMessageModel]


class HealthResponse(BaseModel):
    """Liveness payload. ``degraded`` still returns HTTP 200 so the container stays up."""

    status: Literal["ok", "degraded"]
    backend: Literal["local", "openai"]
    ready: bool
    detail: str
    tool_count: int
    model: str | None


def _check_session_id(session_id: str) -> str:
    if not _SESSION_ID.fullmatch(session_id):
        raise HTTPException(
            status_code=422,
            detail="session_id must be 8-64 characters of letters, numbers, underscores, or hyphens.",
        )
    return session_id


def _new_session_id() -> str:
    return uuid4().hex


def create_app(backend: AgentBackend | None = None) -> FastAPI:
    """Build the API. Tests pass a backend; ``uvicorn`` uses the env default."""
    app = FastAPI(
        title="MCP Server App API",
        version="0.1.0",
        summary="Chat with the LangGraph agent and call MCP tools.",
    )
    app.state.backend = backend or resolve_backend()
    app.state.sessions = SessionStore()

    origins = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
        if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Accept"],
    )

    @app.exception_handler(ToolNotFoundError)
    async def _unknown_tool(_request: Any, exc: ToolNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": f"Unknown tool '{exc.name}'."})

    @app.exception_handler(ToolExecutionError)
    async def _tool_failed(_request: Any, exc: ToolExecutionError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(BackendNotReady)
    async def _backend_not_ready(_request: Any, exc: BackendNotReady) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.get("/")
    async def root() -> dict[str, str]:
        """Point browsers that hit the API port at the useful URLs."""
        return {
            "service": "mcp-server-app-api",
            "health": "/health",
            "docs": "/docs",
            "tools": "/api/tools",
            "chat": "/api/chat",
        }

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        """Report which backend will answer chat, without calling OpenAI."""
        selected: AgentBackend = app.state.backend
        ready, detail = selected.readiness()
        tools = await selected.list_tools()
        model = openai_model_name() if selected.name == "openai" else None
        return HealthResponse(
            status="ok" if ready else "degraded",
            backend="openai" if selected.name == "openai" else "local",
            ready=ready,
            detail=detail,
            tool_count=len(tools),
            model=model,
        )

    @app.get("/api/tools", response_model=list[ToolInfoModel])
    async def list_tools() -> list[ToolInfoModel]:
        """List MCP tools the sidebar and the tool runner can use."""
        tools = await app.state.backend.list_tools()
        return [ToolInfoModel(name=tool.name, description=tool.description) for tool in tools]

    @app.post("/api/tools/call", response_model=ToolCallResponse)
    async def call_tool(body: ToolCallRequest) -> ToolCallResponse:
        """Run one MCP tool with JSON arguments. No model is involved."""
        result = await app.state.backend.call_tool(body.name, body.arguments)
        return ToolCallResponse(name=body.name, result=result)

    @app.post("/api/chat", response_model=ChatResponse)
    async def chat(body: ChatRequest) -> ChatResponse:
        """Send one user message. Creates a session when ``session_id`` is omitted."""
        session_id = _check_session_id(body.session_id) if body.session_id else _new_session_id()
        store: SessionStore = app.state.sessions
        prior = await store.history(session_id)
        history = [
            {"role": item["role"], "content": item["content"]}
            for item in prior
            if item.get("role") in {"user", "assistant"} and item.get("content")
        ]
        turn = await app.state.backend.chat(
            body.message,
            history,
            use_state_graph=body.agent == "state_graph",
        )
        traces = [
            ToolTraceModel(name=trace.name, arguments=trace.arguments, result=trace.result)
            for trace in turn.tool_calls
        ]
        await store.append(session_id, {"role": "user", "content": body.message, "tool_calls": []})
        await store.append(
            session_id,
            {
                "role": "assistant",
                "content": turn.reply,
                "tool_calls": [trace.model_dump() for trace in traces],
            },
        )
        backend_name: Literal["local", "openai"] = "openai" if turn.backend == "openai" else "local"
        return ChatResponse(
            session_id=session_id,
            reply=turn.reply,
            backend=backend_name,
            agent=body.agent,
            tool_calls=traces,
        )

    @app.get("/api/sessions/{session_id}", response_model=SessionResponse)
    async def get_session(session_id: str) -> SessionResponse:
        """Return the transcript stored for ``session_id``."""
        _check_session_id(session_id)
        messages = await app.state.sessions.history(session_id)
        return SessionResponse(
            session_id=session_id,
            messages=[ChatMessageModel.model_validate(item) for item in messages],
        )

    @app.delete("/api/sessions/{session_id}", status_code=204)
    async def delete_session(session_id: str) -> None:
        """Forget a transcript. The browser calls this for "New chat"."""
        _check_session_id(session_id)
        await app.state.sessions.delete(session_id)

    return app


# Used by ``uvicorn api.app:app``. Tests call ``create_app`` directly so they
# can inject a backend and ignore whatever ``AGENT_MODE`` the developer exported.
catalog = ToolCatalog()
app = create_app(resolve_backend(catalog))
