"""Prove the stdio MCP child can list tools and roll dice.

This is the same transport the LangGraph agent uses. It does not call OpenAI.
"""

import os
import sys

import pytest
from langchain_mcp_adapters.client import MultiServerMCPClient

from client.langgraph_agent import build_mcp_config

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.mark.asyncio
async def test_stdio_server_rolls_dice() -> None:
    """Spawn ``run_server.py`` and invoke ``roll_dice`` through MCP."""
    config = build_mcp_config(PROJECT_ROOT)
    server = config["my-mcp-server"]
    # Use this interpreter so the test passes in Docker (python) and locally
    # (the project venv) without depending on ``uv`` being installed.
    server["command"] = sys.executable
    server["args"] = ["run_server.py"]
    server["cwd"] = PROJECT_ROOT
    server["env"]["TAVILY_API_KEY"] = ""

    client = MultiServerMCPClient(config)
    tools = await client.get_tools()
    names = [tool.name for tool in tools]
    assert "roll_dice" in names

    roller = next(tool for tool in tools if tool.name == "roll_dice")
    result = await roller.ainvoke({"notation": "1d6"})
    assert "ROLLS:" in str(result)
