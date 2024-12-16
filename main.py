#
# (c) Copyright Ascensio System SIA 2024
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

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import SimpleEventIsolation
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp.web import Application, run_app
from dotenv import load_dotenv
from redis import Redis

from app import remove_commands, set_commands, setup_handlers, setup_routers
from app.description import set_description
from app.middlewares import setup_middlewares
from config import (
    BOT_TOKEN,
    REDIS_DB,
    REDIS_HOST,
    REDIS_PORT,
    WEB_APP_URL,
    WEBHOOK_HOST,
    WEBHOOK_PATH,
    WEBHOOK_PORT,
)

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_bot() -> Bot:
    return Bot(
        BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML, link_preview_is_disabled=True
        ),
    )


def create_redis_client() -> Redis:
    return Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)


def create_redis_storage() -> Redis:
    return RedisStorage.from_url(
        f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}",
        key_builder=DefaultKeyBuilder(with_destiny=True),
    )


def create_dispatcher(redis_client: Redis, redis_storage: RedisStorage) -> Dispatcher:
    dispatcher = Dispatcher(
        storage=redis_storage, events_isolation=SimpleEventIsolation()
    )
    dispatcher["base_url"] = WEB_APP_URL
    dispatcher["r"] = redis_client
    return dispatcher


def create_app(bot: Bot, redis_client: Redis) -> Application:
    app = Application()
    app["bot"] = bot
    app["r"] = redis_client
    return app


async def on_startup(app: Application) -> None:
    bot = app["bot"]
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await bot.set_webhook(f"{WEB_APP_URL}{WEBHOOK_PATH}")
        await set_commands(bot)
        await set_description(bot)
    except Exception as e:
        logger.error(f"Error on startup: {e}")


async def on_shutdown(app: Application) -> None:
    bot = app["bot"]
    try:
        await remove_commands(bot)
    except Exception as e:
        logger.error(f"Error on shutdown: {e}")


def main() -> None:
    bot = create_bot()
    redis_client = create_redis_client()
    redis_storage = create_redis_storage()
    dispatcher = create_dispatcher(redis_client, redis_storage)
    app = create_app(bot, redis_client)

    dispatcher.startup.register(on_startup)
    dispatcher.shutdown.register(on_shutdown)

    setup_middlewares(dispatcher)
    setup_handlers(dispatcher)
    setup_routers(app)
    setup_application(app, dispatcher, bot=bot)

    SimpleRequestHandler(dispatcher=dispatcher, bot=bot).register(
        app, path=WEBHOOK_PATH
    )
    run_app(app, host=WEBHOOK_HOST, port=WEBHOOK_PORT)


if __name__ == "__main__":
    asyncio.run(main())
