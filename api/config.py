"""Environment helpers for the chat API.

Placeholder values from ``.env.sample`` must not be treated as live
credentials. Docker Compose can start from that file, and the UI should
fall back to local tool routing instead of calling OpenAI with a dummy key.
"""

import os

# Values that ship in .env.sample, plus a few common stand-ins.
_PLACEHOLDERS = {
    "",
    "none",
    "null",
    "changeme",
    "your_openai_api_key_here",
    "your_tavily_api_key_here",
    "your_unsplash_access_key_here",
    "your_langchain_api_key_here",
    "ghp_your_github_personal_access_token_here",
}


def openai_key_is_usable(key: str | None = None) -> bool:
    """Return True when ``key`` (or ``OPENAI_API_KEY``) can be sent to OpenAI."""
    candidate = os.getenv("OPENAI_API_KEY") if key is None else key
    if candidate is None:
        return False
    stripped = candidate.strip()
    lowered = stripped.lower()
    if lowered in _PLACEHOLDERS or lowered.startswith("your_"):
        return False
    if "your_" in lowered:
        return False
    return True


def agent_mode() -> str:
    """Return ``local``, ``openai``, or ``auto`` (the default)."""
    raw = os.getenv("AGENT_MODE", "auto").strip().lower()
    if raw in {"local", "openai", "auto"}:
        return raw
    return "auto"


def openai_model_name() -> str:
    """Model id passed to ChatOpenAI. Defaults to the project's cheap model."""
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
