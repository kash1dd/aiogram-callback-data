from __future__ import annotations

from typing import Any, TypeVar, ClassVar

from pydantic import BaseModel

from aiogram_callback_data.storages.base import BaseStorage
from aiogram_callback_data.callback_data.filter import CallbackDataFilter


__all__ = ("CallbackData",)


T = TypeVar("T", bound="CallbackData")

_MAX_CALLBACK_DATA_BYTES = 64
_HASH_LEN = 32
_MAX_PREFIX_LEN = _MAX_CALLBACK_DATA_BYTES - 1 - _HASH_LEN


class CallbackData(BaseModel):
    """
    Base class for callback data models backed by an external storage.

    Unlike aiogram's built-in ``CallbackData``, payloads are not serialized into
    the 64-byte ``callback_data`` field itself. Instead, the full payload is
    saved in a :class:`BaseStorage` and only a short lookup key of the form
    ``"<prefix>:<hash>"`` is sent to Telegram. This removes the 64-byte limit
    and allows arbitrarily large or nested models.

    Subclasses must declare a unique ``prefix`` used in the storage key::

        class UserAction(CallbackData, prefix="user"):
            user_id: int
            action: str
    """

    __prefix__: ClassVar[str]
    __storage__: ClassVar[BaseStorage | None] = None

    def __init_subclass__(cls, prefix: str, **kwargs: Any) -> None:
        if ":" in prefix:
            raise ValueError(f"Prefix {prefix!r} must not contain ':'")
        if not prefix:
            raise ValueError("Prefix must be a non-empty string")
        if len(prefix) > _MAX_PREFIX_LEN:
            raise ValueError(
                f"Prefix {prefix!r} is too long: max {_MAX_PREFIX_LEN} chars "
                f"(64-byte callback_data limit minus ':' and 32-char hash)"
            )
        cls.__prefix__ = prefix
        super().__init_subclass__(**kwargs)

    @classmethod
    def set_storage(cls, storage: BaseStorage) -> None:
        CallbackData.__storage__ = storage

    @classmethod
    def get_storage(cls) -> BaseStorage:
        if cls.__storage__ is None:
            raise ValueError(f"Storage is not set, call {cls.__name__}.set_storage() first")

        return cls.__storage__

    async def pack(self, ttl: int | None = None) -> str:
        data = self.model_dump_json()
        storage = self.get_storage()

        key = f"{self.__prefix__}:{storage.generate_key(data=data)}"
        await storage.set(key, data, ttl)
        return key

    @classmethod
    async def unpack(cls: type[T], key: str, *, once: bool = False) -> T | None:
        storage = cls.get_storage()
        if once:
            data = await storage.get_and_delete(key)
        else:
            data = await storage.get(key)
        if data is None:
            return None
        return cls.model_validate_json(data)

    @classmethod
    def filter(cls, *, once: bool = False) -> CallbackDataFilter:
        """
        Build an aiogram filter for this callback data class.

        :param once: If ``True``, the storage entry is deleted on first match,
            so the same button can be used exactly once.
        """
        return CallbackDataFilter(cls, once=once)
