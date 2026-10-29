#!/usr/bin/env python3
"""Start the chat API.

The browser UI talks to this process. The process talks to the MCP server
over stdio when the OpenAI backend is active, and calls tools in-process
for the tool runner and for local mode.

Examples:
    uv run python run_api.py
    API_PORT=8000 uv run python run_api.py
"""

import os

import uvicorn
from dotenv import load_dotenv


def main() -> None:
    """Load ``.env`` and serve the FastAPI app."""
    load_dotenv()
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "0") == "1"
    uvicorn.run("api.app:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    main()
