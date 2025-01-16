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

from aiogram.filters import BaseFilter
from aiogram.types import Message

from app.utils.file_utils import get_extension_by_name, get_format_by_extension
from app.utils.lang_utils import _


class DocumentEditFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        async def process_message(reply=False) -> bool:
            if message.chat.type != "private":
                return False

            if message.document:
                extension = get_extension_by_name(message.document.file_name)
                f = get_format_by_extension(extension)
                if f and f["actions"]:
                    return {"f": f, "reply": reply}
                return await message.answer(_("File not supported"))

            if message.photo:
                return await message.answer(_("File not supported"))

            return False

        result = await process_message()
        if result:
            return result

        if message.reply_to_message:
            message = message.reply_to_message
            return await process_message(reply=True)

        return False
