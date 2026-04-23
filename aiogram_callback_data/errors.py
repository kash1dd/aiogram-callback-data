from __future__ import annotations


class CallbackDataError(Exception):
    """Base exception for CallbackData errors."""


class HashNotFoundError(CallbackDataError):
    """Hash not found in storage."""

    def __init__(self, key: str) -> None:
        super().__init__(key)
        self.key = key

    def __str__(self) -> str:
        return f"Callback data for key {self.key!r} not found in storage (missing or expired)"
