"""HTTP tests for the chat API.

The dice path uses the real MCP tool. The OpenAI path is covered with a
stand-in backend so the suite never calls the network for a model.
"""

import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from api.backends import ChatTurn, LocalToolBackend, ToolTrace
from api.catalog import ToolCatalog
from api.config import openai_key_is_usable


class _RecordingBackend:
    """Stand-in that records history and echoes the user message."""

    name = "openai"

    def __init__(self) -> None:
        self.history: list[dict[str, str]] = []
        self.use_state_graph = False

    def readiness(self) -> tuple[bool, str]:
        return True, "Recording backend is ready."

    async def list_tools(self) -> list:
        return []

    async def call_tool(self, name: str, arguments: dict) -> str:
        return f"{name} ok"

    async def chat(self, message: str, history: list[dict[str, str]], use_state_graph: bool) -> ChatTurn:
        self.history = history
        self.use_state_graph = use_state_graph
        return ChatTurn(
            reply=f"echo: {message}",
            backend="openai",
            tool_calls=[ToolTrace(name="roll_dice", arguments={"notation": "1d6"}, result="ROLLS: 4")],
        )


@pytest.fixture
def local_client() -> TestClient:
    """API wired to the real in-process tools, never to OpenAI."""
    return TestClient(create_app(LocalToolBackend(ToolCatalog())))


def test_health_lists_tools(local_client: TestClient) -> None:
    response = local_client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["backend"] == "local"
    assert body["ready"] is True
    assert body["tool_count"] == 10
    assert body["model"] is None


def test_list_tools_includes_dice(local_client: TestClient) -> None:
    response = local_client.get("/api/tools")
    assert response.status_code == 200
    names = [tool["name"] for tool in response.json()]
    assert "roll_dice" in names
    assert "web_search" in names
    assert len(names) == 10


def test_direct_dice_call(local_client: TestClient) -> None:
    response = local_client.post(
        "/api/tools/call",
        json={"name": "roll_dice", "arguments": {"notation": "1d20"}},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "roll_dice"
    assert "ROLLS:" in body["result"]
    assert "RETURNS:" in body["result"]


def test_unknown_tool_is_404(local_client: TestClient) -> None:
    response = local_client.post("/api/tools/call", json={"name": "not_a_tool", "arguments": {}})
    assert response.status_code == 404
    assert "not_a_tool" in response.json()["detail"]


def test_invalid_dice_notation_is_400(local_client: TestClient) -> None:
    response = local_client.post(
        "/api/tools/call",
        json={"name": "roll_dice", "arguments": {"notation": "banana"}},
    )
    assert response.status_code == 400


def test_local_chat_rolls_dice_and_keeps_session(local_client: TestClient) -> None:
    first = local_client.post("/api/chat", json={"message": "Please roll 2d6"})
    assert first.status_code == 200
    body = first.json()
    assert body["backend"] == "local"
    assert "ROLLS:" in body["reply"]
    assert body["tool_calls"][0]["name"] == "roll_dice"
    assert body["tool_calls"][0]["arguments"]["notation"] == "2d6"

    session_id = body["session_id"]
    transcript = local_client.get(f"/api/sessions/{session_id}")
    assert transcript.status_code == 200
    roles = [item["role"] for item in transcript.json()["messages"]]
    assert roles == ["user", "assistant"]

    deleted = local_client.delete(f"/api/sessions/{session_id}")
    assert deleted.status_code == 204
    assert local_client.get(f"/api/sessions/{session_id}").json()["messages"] == []


def test_local_chat_without_a_tool_explains_itself(local_client: TestClient) -> None:
    response = local_client.post("/api/chat", json={"message": "hello there"})
    assert response.status_code == 200
    body = response.json()
    assert body["tool_calls"] == []
    assert "local mode" in body["reply"].lower()


def test_empty_message_is_rejected(local_client: TestClient) -> None:
    response = local_client.post("/api/chat", json={"message": "   "})
    assert response.status_code == 422


def test_bad_session_id_is_rejected(local_client: TestClient) -> None:
    response = local_client.post("/api/chat", json={"message": "Roll 1d6", "session_id": "../etc"})
    assert response.status_code == 422


def test_recording_backend_receives_history_and_graph_choice() -> None:
    backend = _RecordingBackend()
    client = TestClient(create_app(backend))
    created = client.post("/api/chat", json={"message": "first", "session_id": "session-one"})
    assert created.status_code == 200
    assert created.json()["reply"] == "echo: first"
    assert created.json()["tool_calls"][0]["result"] == "ROLLS: 4"

    follow = client.post(
        "/api/chat",
        json={"message": "second", "session_id": "session-one", "agent": "state_graph"},
    )
    assert follow.status_code == 200
    assert backend.use_state_graph is True
    assert backend.history == [{"role": "user", "content": "first"}, {"role": "assistant", "content": "echo: first"}]


def test_placeholder_openai_key_selects_local_mode(monkeypatch) -> None:
    monkeypatch.setenv("AGENT_MODE", "auto")
    monkeypatch.setenv("OPENAI_API_KEY", "your_openai_api_key_here")
    assert openai_key_is_usable() is False
    client = TestClient(create_app())
    body = client.get("/health").json()
    assert body["backend"] == "local"
    assert "your_openai_api_key_here" not in str(body)


def test_openai_mode_without_a_key_is_degraded(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("AGENT_MODE", "openai")
    client = TestClient(create_app())
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["ready"] is False
    assert health.json()["status"] == "degraded"
    chat = client.post("/api/chat", json={"message": "Roll 1d6"})
    assert chat.status_code == 503
    assert "OPENAI_API_KEY" in chat.json()["detail"]


def test_health_does_not_echo_a_configured_key(monkeypatch) -> None:
    monkeypatch.setenv("AGENT_MODE", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-secret-value")
    client = TestClient(create_app())
    assert "sk-test-secret-value" not in client.get("/health").text
