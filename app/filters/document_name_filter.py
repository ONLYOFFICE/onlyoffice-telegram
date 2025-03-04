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

import unicodedata

from aiogram.filters import BaseFilter
from aiogram.types import Message


class DocumentNameFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        def filter_characters(file_name):
            allowed_chars = " !#$%&()+,;=@^_-}{~."
            filtered_chars = []
            for char in file_name:
                if unicodedata.category(char).startswith("L") or char.isdigit():
                    filtered_chars.append(char)
                elif char in allowed_chars:
                    filtered_chars.append(char)
            filtered_chars = "".join(filtered_chars)
            filtered_chars = filtered_chars.lstrip(" &.").rstrip(" &.")
            return filtered_chars

        if message.text:
            file_name = filter_characters(message.text)
            if len(file_name) > 60 or len(file_name) <= 0:
                return False
            return {"file_name": file_name}
        return False
