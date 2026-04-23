from __future__ import annotations

from typing import Any

from redis.asyncio import Redis, ConnectionPool

from aiogram_callback_data.storages.base import BaseStorage


__all__ = ("RedisStorage",)


class RedisStorage(BaseStorage):
    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    @classmethod
    def from_url(cls, url: str, **kwargs: Any) -> RedisStorage:
        return cls(Redis.from_url(url, **kwargs))

    @classmethod
    def from_pool(cls, pool: ConnectionPool) -> RedisStorage:
        return cls(Redis.from_pool(pool))

    async def set(self, key: str, data: str, ttl: int | None = None) -> None:
        if ttl is not None and ttl <= 0:
            raise ValueError(f"ttl must be positive, got {ttl}")
        await self.redis.set(key, data, ex=ttl)

    async def get(self, key: str) -> str | None:
        value = await self.redis.get(key)
        if value is None:
            return None
        if isinstance(value, bytes):
            return value.decode()
        return str(value)

    async def delete(self, key: str) -> None:
        await self.redis.delete(key)

    async def get_and_delete(self, key: str) -> str | None:
        value = await self.redis.getdel(key)
        if value is None:
            return None
        if isinstance(value, bytes):
            return value.decode()
        return str(value)
