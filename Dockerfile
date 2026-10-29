# API image: FastAPI, the LangGraph client, and the MCP server it can spawn.
# The web UI is a separate image. See docker-compose.yml.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    MCP_COMMAND=python \
    MCP_ARGS=run_server.py \
    AGENT_MODE=auto \
    API_HOST=0.0.0.0 \
    API_PORT=8000

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /uvx /bin/

# Dependencies first so code edits do not reinstall the whole virtualenv.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY server ./server
COPY client ./client
COPY api ./api
COPY tests ./tests
COPY examples ./examples
COPY run_server.py run_client.py run_api.py README.md ./

RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["python", "run_api.py"]
