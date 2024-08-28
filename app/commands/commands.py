from aiogram import Bot
from aiogram.types import (
    BotCommand,
    BotCommandScopeChat,
    BotCommandScopeDefault,
    MenuButtonDefault,
)

from app.utils.lang_utils import _, i18n


def get_commands(lang: str = "en"):
    commands = [
        BotCommand(command="/start", description=_("Start", locale=lang)),
        BotCommand(command="/cancel", description=_("Cancel", locale=lang)),
        BotCommand(command="/lang", description=_("Change language", locale=lang)),
    ]

    return commands


async def set_commands(bot: Bot):
    await bot.set_my_commands(get_commands(), scope=BotCommandScopeDefault())
    for lang in i18n.available_locales:
        await bot.set_my_commands(
            get_commands(lang), scope=BotCommandScopeDefault(), language_code=lang
        )
    await bot.set_chat_menu_button(menu_button=MenuButtonDefault())


async def remove_commands(bot: Bot, id: int = None):
    scope = BotCommandScopeChat(chat_id=id) if id else BotCommandScopeDefault()
    await bot.delete_my_commands(scope=scope)
    for lang in i18n.available_locales:
        await bot.delete_my_commands(scope=scope, language_code=lang)
