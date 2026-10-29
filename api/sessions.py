"""In-memory chat sessions for a single API process.

This is enough for a local Docker demo. A restart forgets every session,
and two API replicas would not share them. ``PRODUCTIONIZING.md`` covers
moving this store to Redis before running more than one instance.
"""

import asyncio
from typing import Any


class SessionStore:
    """Append-only transcript keyed by a client-visible session id."""

    def __init__(self, max_messages: int = 40) -> None:
        self._sessions: dict[str, list[dict[str, Any]]] = {}
        self._lock = asyncio.Lock()
        self._max_messages = max_messages

    async def history(self, session_id: str) -> list[dict[str, Any]]:
        """Return a copy of the transcript. Missing sessions are empty."""
        async with self._lock:
            return [dict(item) for item in self._sessions.get(session_id, [])]

    async def append(self, session_id: str, message: dict[str, Any]) -> list[dict[str, Any]]:
        """Append one message and return the trimmed transcript."""
        async with self._lock:
            bucket = self._sessions.setdefault(session_id, [])
            bucket.append(dict(message))
            overflow = len(bucket) - self._max_messages
            if overflow > 0:
                del bucket[:overflow]
            return [dict(item) for item in bucket]

    async def delete(self, session_id: str) -> None:
        """Drop a session. Deleting an unknown id is a no-op."""
        async with self._lock:
            self._sessions.pop(session_id, None)
