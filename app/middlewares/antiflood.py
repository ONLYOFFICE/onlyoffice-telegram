#
# (c) Copyright Ascensio System SIA 2025
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from __future__ import annotations

import logging
import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.enums import ChatType, ContentType
from aiogram.types import Message
from redis import Redis

from app.utils.lang_utils import _
from config import BOT_NAME, FLOOD_INTERVAL, FLOOD_MESSAGES_LIMIT, FLOOD_TTL

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
            message = getattr(event, "message", None)
            if message and (message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]):
                if message.content_type not in [ContentType.TEXT, ContentType.DOCUMENT]:
                    return
                if await data["state"].get_state() is not None:
                    await self.on_process_event(event.event, data["r"])
                elif message.text and BOT_NAME in message.text:
                    await self.on_process_event(event.event, data["r"])
                elif message.caption and BOT_NAME in message.caption:
                    await self.on_process_event(event.event, data["r"])
                else:
                    return
            else:
                await self.on_process_event(event.event, data["r"])
        except CancelHandler:
            return

        try:
            return await handler(event, data)
        except Exception as e:
            logger.error(e)

    async def on_process_event(self, event: Message, r: Redis) -> None:
        user_id = event.from_user.id
        media_group_id = getattr(event, "media_group_id", None)
        try:
            await self.check_throttling(user_id, media_group_id, r)
        except Throttled as t:
            if t.exceeded_count == FLOOD_MESSAGES_LIMIT:
                await self.event_throttled(event, t)
            raise CancelHandler() from t

    async def event_throttled(self, event: Message, throttled: Throttled) -> None:
        delta = FLOOD_INTERVAL - throttled.delta
        await event.answer(_("Too many requests, try again in {delta:.2f} seconds").format(delta=delta))

    async def check_throttling(self, user_id: int, media_group_id: str | bool, r: Redis):
        try:
            media_group_id = int(media_group_id)
        except (ValueError, TypeError):
            media_group_id = 0
        now = time.time()
        key = f"{user_id}:throttle"

        result = r.hgetall(key)
        data = {field.decode("utf-8"): value.decode("utf-8") for field, value in result.items()}

        last_message = float(data.get("last_message", now))
        exceeded_count = int(data.get("exceeded_count", 0))
        last_media_group_id = int(data.get("last_media_group_id", 0))

        if last_media_group_id and last_media_group_id == media_group_id:
            return

        delta = now - last_message

        if delta < FLOOD_INTERVAL:
            exceeded_count += 1
        else:
            exceeded_count = 1

        # Update Redis
        data["last_message"] = now
        data["delta"] = delta
        data["exceeded_count"] = exceeded_count
        data["last_media_group_id"] = media_group_id

        r.hset(key, mapping=data)
        r.expire(key, FLOOD_TTL)

        if exceeded_count >= FLOOD_MESSAGES_LIMIT:
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
