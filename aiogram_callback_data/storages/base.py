from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod


__all__ = ("BaseStorage",)


class BaseStorage(ABC):
    """
    Abstract base class for callback data storage.
    """

    @abstractmethod
    async def set(self, key: str, data: str, ttl: int | None = None) -> None:
        """
        Store serialized callback data by key.

        :param key: Unique short key (will be placed into callback_data).
        :param data: Full serialized callback data string.
        :param ttl: Time-to-live in seconds. None = no expiration.
        """

    @abstractmethod
    async def get(self, key: str) -> str | None:
        """
        Retrieve serialized callback data by key.

        :param key: The short key from callback_data.
        :return: Full serialized data string or None if not found / expired.
        """

    @abstractmethod
    async def delete(self, key: str) -> None:
        """
        Delete serialized callback data by key.

        :param key: The key from callback_data.
        """

    @abstractmethod
    async def get_and_delete(self, key: str) -> str | None:
        """
        Atomically retrieve and delete serialized callback data by key.

        Used for one-shot buttons: the entry is removed on first access so
        subsequent clicks on the same button return ``None``.

        :param key: The short key from callback_data.
        :return: Full serialized data string or None if not found / expired.
        """

    def generate_key(self, data: str) -> str:
        """
        Generate a hash key from the serialized data (md5 hex, 32 chars).
        """

        return hashlib.md5(data.encode()).hexdigest()
