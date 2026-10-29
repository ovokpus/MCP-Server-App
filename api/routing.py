"""Decide which MCP tools a local-mode message should run.

Local mode is the path used when no OpenAI key is configured. It is a
small router, not a model: it looks for dice notation and a handful of
phrases, then calls the matching tools. The LangGraph agent replaces this
when ``OPENAI_API_KEY`` is real.
"""

import re

# Keep the child (and the request) from looping on a huge "roll 9999 times".
_MAX_ROLLS = 20
_MAX_CALLS = 4

_DICE = re.compile(r"(\d+d\d+(?:k\d+)?)", re.IGNORECASE)
_BARE_DIE = re.compile(r"(?<!\d)d(\d+)\b", re.IGNORECASE)
_REPEAT = re.compile(r"(\d+)\s*(?:times|rolls)\b", re.IGNORECASE)
_ABOUT = re.compile(r"\babout\s+(.+)$", re.IGNORECASE)
_GITHUB_FILLER = re.compile(
    r"\b(please|search|github|repositories|repository|repos|repo|for|the|a|an|my)\b",
    re.IGNORECASE,
)


def _about(text: str, fallback: str) -> str:
    match = _ABOUT.search(text.strip())
    if not match:
        return fallback
    topic = match.group(1).strip(" .!?\"'")
    return topic or fallback


def _dice_call(text: str) -> tuple[str, dict[str, int | str]] | None:
    match = _DICE.search(text)
    if match:
        notation = match.group(1)
    else:
        bare = _BARE_DIE.search(text)
        if not bare:
            return None
        notation = f"1d{bare.group(1)}"

    repeats = _REPEAT.search(text)
    num_rolls = int(repeats.group(1)) if repeats else 1
    num_rolls = max(1, min(num_rolls, _MAX_ROLLS))
    return ("roll_dice", {"notation": notation, "num_rolls": num_rolls})


def plan_local_calls(message: str) -> list[tuple[str, dict[str, object]]]:
    """Return ordered ``(tool_name, arguments)`` pairs for ``message``.

    An empty list means the router did not recognize a tool request. The
    caller should explain what local mode can do instead of guessing.
    """
    text = message.strip()
    lowered = text.lower()
    calls: list[tuple[str, dict[str, object]]] = []

    dice = _dice_call(text)
    if dice is not None:
        calls.append(dice)

    if any(phrase in lowered for phrase in ("social post", "linkedin", "instagram", "social media")):
        style = "casual" if any(word in lowered for word in ("casual", "fun", "playful")) else "professional"
        calls.append(("create_social_post", {"topic": _about(text, text[:240]), "style": style}))

    if any(phrase in lowered for phrase in ("slide", "presentation image", "presentation-ready")):
        calls.append(("get_slide_image", {"topic": _about(text, "presentation"), "size": "1920x1080"}))

    if "quote" in lowered:
        calls.append(("create_quote_card", {"theme": _about(text, "motivation")}))

    wants_github = "github" in lowered
    if wants_github:
        query = _GITHUB_FILLER.sub(" ", text)
        query = " ".join(query.split()) or "mcp"
        calls.append(("github_search_repositories", {"query": query[:200], "limit": 5}))

    wants_web = (not wants_github) and any(
        phrase in lowered for phrase in ("search the web", "web search", "look up", "news", "search for")
    )
    if wants_web:
        calls.append(("web_search", {"query": text[:400]}))

    return calls[:_MAX_CALLS]
