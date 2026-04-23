from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram.types import CallbackQuery
from aiogram.filters import BaseFilter

from aiogram_callback_data.errors import HashNotFoundError
from aiogram_callback_data.storages.base import BaseStorage


if TYPE_CHECKING:
    from aiogram_callback_data.callback_data.callback_data import CallbackData


__all__ = ("CallbackDataFilter",)


class CallbackDataFilter(BaseFilter):
    """
    aiogram filter that resolves callback keys into ``CallbackData`` objects.

    Created via :meth:`CallbackData.filter`. When a ``CallbackQuery`` arrives,
    the filter splits ``call.data`` on ``":"``, matches the prefix against the
    bound class and — on match — loads the payload from storage and validates
    it directly from JSON::

        @router.callback_query(UserAction.filter())
        async def handle(call: CallbackQuery, callback_data: UserAction): ...
    """

    def __init__(self, callback_data_cls: type[CallbackData], *, once: bool = False) -> None:
        self.callback_data_cls = callback_data_cls
        self.once = once

    async def __call__(
        self, call: CallbackQuery, callback_data_storage: BaseStorage
    ) -> bool | dict[str, Any]:
        raw = call.data
        if not raw:
            return False

        prefix, sep, _ = raw.partition(":")
        if not sep or prefix != self.callback_data_cls.__prefix__:
            return False

        obj = await self.callback_data_cls.unpack(raw, once=self.once)
        if obj is None:
            raise HashNotFoundError(raw)

        return {"callback_data": obj}
