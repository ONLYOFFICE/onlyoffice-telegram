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

from aiogram import Bot
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeChat,
    BotCommandScopeDefault,
    MenuButtonDefault,
)

from app.utils.lang_utils import _, i18n


def get_private_chats_commands(lang: str = "en") -> list[BotCommand]:
    commands = [
        BotCommand(command="/start", description=_("Start", locale=lang)),
        BotCommand(command="/lang", description=_("Change language", locale=lang)),
        BotCommand(command="/help", description=_("Help", locale=lang)),
        BotCommand(command="/cancel", description=_("Cancel", locale=lang)),
    ]
    return commands


def get_group_chats_commands(lang: str = "en") -> list[BotCommand]:
    commands = [
        BotCommand(command="/document", description=_("Create document", locale=lang)),
        BotCommand(command="/spreadsheet", description=_("Create spreadsheet", locale=lang)),
        BotCommand(command="/presentation", description=_("Create presentation", locale=lang)),
        BotCommand(command="/open", description=_("Open", locale=lang)),
        BotCommand(command="/help", description=_("Help", locale=lang)),
        BotCommand(command="/cancel", description=_("Cancel", locale=lang)),
    ]
    return commands


async def set_commands(bot: Bot):
    await bot.set_my_commands(get_private_chats_commands(), scope=BotCommandScopeDefault())
    for lang in i18n.available_locales:
        await bot.set_my_commands(
            get_private_chats_commands(lang),
            scope=BotCommandScopeAllPrivateChats(),
            language_code=lang,
        )

    await bot.set_my_commands(get_group_chats_commands(), scope=BotCommandScopeAllGroupChats())
    for lang in i18n.available_locales:
        await bot.set_my_commands(
            get_group_chats_commands(lang),
            scope=BotCommandScopeAllGroupChats(),
            language_code=lang,
        )

    await bot.set_chat_menu_button(menu_button=MenuButtonDefault())


async def remove_commands(bot: Bot, chat_id: int = None):
    scope = BotCommandScopeChat(chat_id=chat_id) if chat_id else BotCommandScopeDefault()
    await bot.delete_my_commands(scope=scope)
    for lang in i18n.available_locales:
        await bot.delete_my_commands(scope=scope, language_code=lang)
