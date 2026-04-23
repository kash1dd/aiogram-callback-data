from __future__ import annotations

import time

from aiogram_callback_data.storages.base import BaseStorage


__all__ = ("InMemoryStorage",)


class InMemoryStorage(BaseStorage):
    """
    Simple in-memory storage (dict-based).

    Good for development / single-process bots.
    For production with multiple workers use Redis-based storage.

    Supports optional TTL — expired entries are cleaned lazily on access
    and periodically via :meth:`cleanup`.
    """

    def __init__(self) -> None:
        # key -> (data, expires_at | None)
        self._store: dict[str, tuple[str, float | None]] = {}

    async def set(self, key: str, data: str, ttl: int | None = None) -> None:
        if ttl is not None and ttl <= 0:
            raise ValueError(f"ttl must be positive, got {ttl}")
        expires_at = (time.monotonic() + ttl) if ttl is not None else None
        self._store[key] = (data, expires_at)

    async def get(self, key: str) -> str | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        data, expires_at = entry
        if expires_at is not None and time.monotonic() > expires_at:
            del self._store[key]
            return None
        return data

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def get_and_delete(self, key: str) -> str | None:
        entry = self._store.pop(key, None)
        if entry is None:
            return None
        data, expires_at = entry
        if expires_at is not None and time.monotonic() > expires_at:
            return None
        return data

    async def cleanup(self) -> int:
        """
        Remove all expired entries. Returns the number of removed keys.
        Call periodically if you worry about memory in long-running bots.
        """

        now = time.monotonic()
        expired = [k for k, (_, exp) in self._store.items() if exp is not None and now > exp]
        for k in expired:
            del self._store[k]
        return len(expired)
