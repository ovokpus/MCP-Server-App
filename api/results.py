"""Normalize FastMCP ``call_tool`` return values into plain text.

FastMCP returns either a list of content blocks or a ``(content, metadata)``
tuple when the tool declares a structured output schema. String tools in
this repo currently come back as the tuple form.
"""

from typing import Any


def stringify_tool_result(result: Any) -> str:
    """Render a tool result as the text a person should read."""
    if isinstance(result, tuple) and len(result) == 2:
        content, metadata = result
        if isinstance(metadata, dict) and "result" in metadata:
            return str(metadata["result"])
        result = content

    if isinstance(result, str):
        return result

    if isinstance(result, dict) and "result" in result:
        return str(result["result"])

    if isinstance(result, list):
        parts: list[str] = []
        for block in result:
            text = getattr(block, "text", None)
            if text is None and isinstance(block, dict):
                raw = block.get("text")
                text = raw if isinstance(raw, str) else None
            parts.append(text if text is not None else str(block))
        return "\n".join(parts)

    return str(result)
