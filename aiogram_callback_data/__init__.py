from __future__ import annotations

from aiogram import Dispatcher

from .storages import BaseStorage
from .callback_data import CallbackData, CallbackDataMiddleware


__all__ = (
    "CallbackData",
    "CallbackDataMiddleware",
)


def setup(storage: BaseStorage, dp: Dispatcher) -> None:
    dp.callback_query.outer_middleware(CallbackDataMiddleware(storage=storage))
    CallbackData.set_storage(storage)
