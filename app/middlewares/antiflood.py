from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message
from redis import Redis

from app.utils.lang_utils import _
from config import FLOOD_INTERVAL, FLOOD_MESSAGES_LIMIT, FLOOD_TTL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ThrottlingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        try:
            await self.on_process_event(event.event, data["r"])
        except CancelHandler:
            return

        try:
            return await handler(event, data)
        except Exception as e:
            logger.error(e)

    async def on_process_event(self, event: Message, r: Redis) -> None:
        user_id = event.from_user.id
        try:
            await self.check_throttling(user_id, r)
        except Throttled as t:
            await self.event_throttled(event, t)
            raise CancelHandler()

    async def event_throttled(self, event: Message, throttled: Throttled) -> None:
        delta = FLOOD_INTERVAL - throttled.delta
        await event.answer(
            _("Too many requests, try again in {delta:.2f} seconds").format(delta=delta)
        )
        await asyncio.sleep(delta)

    async def check_throttling(self, user_id: int, r: Redis):
        now = time.time()
        key = f"{user_id}:throttle"

        result = r.hgetall(key)
        data = {
            field.decode("utf-8"): value.decode("utf-8")
            for field, value in result.items()
        }

        last_message = float(data.get("last_message", now))
        exceeded_count = int(data.get("exceeded_count", 0))

        delta = now - last_message

        if delta < FLOOD_INTERVAL:
            exceeded_count += 1
        else:
            exceeded_count = 1

        # Update Redis
        data["last_message"] = now
        data["delta"] = delta
        data["exceeded_count"] = exceeded_count

        r.hset(key, mapping=data)
        r.expire(key, FLOOD_TTL)

        if exceeded_count > FLOOD_MESSAGES_LIMIT:
            raise Throttled(user_id, exceeded_count, delta)


class Throttled(Exception):
    def __init__(self, user_id, exceeded_count, delta):
        self.user_id = user_id
        self.exceeded_count = exceeded_count
        self.delta = delta

    def __str__(self) -> str:
        return (
            f"Rate limit exceeded error"
            f"user_id: {self.user_id},"
            f"exceeded_count: {self.exceeded_count},"
            f"delta: {self.delta:.3f} s)"
        )


class CancelHandler(Exception):
    pass


throttling_middleware = ThrottlingMiddleware()
