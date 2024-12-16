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
