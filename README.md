# aiogram-callback-data

A small extension for [aiogram 3](https://github.com/aiogram/aiogram) that lifts Telegram's 64-byte `callback_data` limit.

Instead of serializing your payload into the callback string itself, this library stores the full payload in an external storage (in-memory or Redis) and sends only a short lookup key to Telegram. This lets you pass arbitrarily large or deeply nested models through inline buttons.

## Features

- Drop-in `CallbackData` base class built on `pydantic.BaseModel`.
- Storage backends: `InMemoryStorage` (dev) and `RedisStorage` (prod).
- Optional TTL on every `pack()` call.
- One-shot buttons — the entry is deleted on the first click.
- Fully typed, compatible with aiogram's filter/DI system.

## Installation (pip)

```bash
pip install aiogram-callback-data

# with Redis support
pip install "aiogram-callback-data[redis]"
```

## Installation (uv)

```bash
uv add aiogram-callback-data

# With Redis support
uv add "aiogram-callback-data[redis]"
```

Python >= 3.10 is required.

## Quick start

```python
from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogram_callback_data import CallbackData, setup
from aiogram_callback_data.storages import InMemoryStorage


bot = Bot(token="YOUR_TOKEN")
dp = Dispatcher()
storage = InMemoryStorage()


class UserAction(CallbackData, prefix="user"):
    user_id: int
    action: str
    # arbitrarily large payload — no 64-byte limit anymore
    context: dict[str, str] = {}


@dp.message()
async def send_menu(msg: Message) -> None:
    builder = InlineKeyboardBuilder()

    approve_key = await UserAction(
        user_id=msg.from_user.id,
        action="approve",
        context={"source": "menu", "version": "v2"},
    ).pack(ttl=300)

    reject_key = await UserAction(
        user_id=msg.from_user.id,
        action="reject",
    ).pack(ttl=300)

    builder.button(text="✅ Approve", callback_data=approve_key)
    builder.button(text="❌ Reject", callback_data=reject_key)

    await msg.answer("Choose:", reply_markup=builder.as_markup())


@dp.callback_query(UserAction.filter())
async def handle_action(call: CallbackQuery, callback_data: UserAction) -> None:
    await call.answer(
        f"User {callback_data.user_id} → {callback_data.action}",
        show_alert=True,
    )


if __name__ == "__main__":
    setup(storage, dp)
    asyncio.run(dp.start_polling(bot))
```

## One-shot buttons

Pass `once=True` to `filter()` to make a button usable exactly once. The storage entry is deleted atomically on the first match, so subsequent clicks raise `HashNotFoundError`.

```python
@dp.callback_query(UserAction.filter(once=True))
async def handle_once(call: CallbackQuery, callback_data: UserAction) -> None:
    await call.answer("Accepted. This button is now dead.")
```

## Redis backend

```python
from aiogram_callback_data.storages import RedisStorage

storage = RedisStorage.from_url("redis://localhost:6379/0")
setup(storage, dp)
```

`RedisStorage` uses `redis.asyncio` under the hood and implements `GETDEL` for one-shot buttons.

## How it works

1. `CallbackData.pack()` dumps the model to JSON, hashes it (md5, 32 chars), builds a key of the form `"<prefix>:<hash>"`, and saves the JSON under that key.
2. Only the short key is sent to Telegram as `callback_data`.
3. On incoming `CallbackQuery`, `CallbackData.filter()` matches the prefix, loads the JSON from storage, and validates it back into your model — which is then injected into the handler as `callback_data`.

Prefix length is capped at **31 characters** (64-byte Telegram limit − `":"` − 32-char hash) and is validated at class-declaration time.

## Error handling

If the storage entry is missing or expired (e.g. the user clicks an old button), the filter raises `HashNotFoundError`:

```python
from aiogram import Router
from aiogram.types import ErrorEvent
from aiogram_callback_data.errors import HashNotFoundError

router = Router()


@router.errors()
async def on_error(event: ErrorEvent) -> bool:
    if isinstance(event.exception, HashNotFoundError):
        call = event.update.callback_query
        if call:
            await call.answer("This button has expired.", show_alert=True)
        return True
    return False
```
