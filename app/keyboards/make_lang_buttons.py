from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.utils.lang_utils import i18n


class LangCallback(CallbackData, prefix="lang"):
    lang: str


def make_lang_buttons() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    [
        builder.button(text=lang.upper(), callback_data=LangCallback(lang=lang))
        for lang in i18n.available_locales
    ]

    return builder.as_markup()
