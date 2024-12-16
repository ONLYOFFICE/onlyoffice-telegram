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

from aiogram import Bot

from app.utils.lang_utils import _, i18n


async def set_description(bot: Bot):
    for lang in i18n.available_locales:
        await bot.set_my_description(
            _(
                "📑 ONLYOFFICE bot can create, open and convert office files\n\n- Create documents, spreadsheets, presentations\n- Open your local files and edit them\n- Collaborate with other people in real time\n- Convert files to multiple formats\n\nPress /start to create/edit files\n",
                locale=lang,
            ),
            language_code=lang,
        )
        await bot.set_my_short_description(
            _(
                "Easily create, convert, edit and collaborate on office files using the ONLYOFFICE bot.",
                locale=lang,
            ),
            language_code=lang,
        )
