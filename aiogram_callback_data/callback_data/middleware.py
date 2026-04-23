from __future__ import annotations

from typing import Any, Callable, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from aiogram_callback_data.storages.base import BaseStorage


__all__ = ("CallbackDataMiddleware",)


class CallbackDataMiddleware(BaseMiddleware):
    """
    aiogram middleware that exposes the callback data storage to handlers.

    Registered on a dispatcher or router, the middleware places the configured
    :class:`BaseStorage` into the per-update ``data`` dict under the
    ``callback_data_storage`` key so that filters and handlers (such as
    :class:`CallbackDataFilter`) can depend on it via standard dependency
    injection::

        dp.callback_query.middleware(CallbackDataMiddleware(storage))
    """

    def __init__(self, storage: BaseStorage) -> None:
        self.storage = storage

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["callback_data_storage"] = self.storage
        return await handler(event, data)
