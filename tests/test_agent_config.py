"""Tests for MCP stdio configuration and tool-trace parsing.

These do not start a model or a server process.
"""

import json

from client.langgraph_agent import build_mcp_config, extract_tool_traces, message_text


class _Msg:
    def __init__(self, **kwargs: object) -> None:
        self.__dict__.update(kwargs)


def test_mcp_config_defaults_to_uv(monkeypatch) -> None:
    monkeypatch.delenv("MCP_COMMAND", raising=False)
    monkeypatch.delenv("MCP_ARGS", raising=False)
    config = build_mcp_config("/work/project")
    server = config["my-mcp-server"]
    assert server["command"] == "uv"
    assert server["args"] == ["--directory", "/work/project", "run", "run_server.py"]
    assert server["transport"] == "stdio"
    assert server["cwd"] == "/work/project"


def test_mcp_config_forwards_parent_environment(monkeypatch) -> None:
    monkeypatch.setenv("MCP_COMMAND", "python")
    monkeypatch.setenv("MCP_ARGS", "run_server.py")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-value")
    config = build_mcp_config("/work/project")
    server = config["my-mcp-server"]
    assert server["command"] == "python"
    assert server["args"] == ["run_server.py"]
    assert server["env"]["TAVILY_API_KEY"] == "tvly-test-value"
    assert "PATH" in server["env"]


def test_mcp_config_accepts_json_args(monkeypatch) -> None:
    monkeypatch.setenv("MCP_COMMAND", "python")
    monkeypatch.setenv("MCP_ARGS", json.dumps(["-m", "server.main"]))
    config = build_mcp_config("/work/project")
    assert config["my-mcp-server"]["args"] == ["-m", "server.main"]


def test_extract_tool_traces_pairs_calls_with_results() -> None:
    messages = [
        _Msg(type="human", content="roll", tool_calls=[]),
        _Msg(
            type="ai",
            content="",
            tool_calls=[{"id": "1", "name": "roll_dice", "args": {"notation": "1d6"}}],
        ),
        _Msg(type="tool", content="ROLLS: 4 -> RETURNS: 4", tool_call_id="1", name="roll_dice"),
        _Msg(type="ai", content="You rolled a 4.", tool_calls=[]),
    ]
    traces = extract_tool_traces(messages)
    assert traces == [
        {"name": "roll_dice", "arguments": {"notation": "1d6"}, "result": "ROLLS: 4 -> RETURNS: 4"}
    ]
    assert message_text([{"type": "text", "text": "hello"}]) == "hello"
