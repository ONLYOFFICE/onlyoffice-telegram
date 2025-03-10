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

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.utils.lang_utils import i18n


class LangCallback(CallbackData, prefix="lang"):
    lang: str
    user_id: int


def make_lang_buttons(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.max_width = 3

    for lang in i18n.available_locales:
        builder.button(text=get_language_name(lang), callback_data=LangCallback(lang=lang, user_id=user_id))

    return builder.as_markup(resize_keyboard=True)


def get_language_name(lang):
    language_map = {
        "de": "Deutsch",
        "en": "English",
        "es": "Español",
        "fr": "Français",
        "it": "Italiano",
        "ja": "日本語",
        "pt": "Português",
        "ru": "Русский",
        "zh": "中文",
    }

    return language_map.get(lang, lang)
