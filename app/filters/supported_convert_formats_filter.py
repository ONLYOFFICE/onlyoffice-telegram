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

from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message


class SupportedConvertFormatsFilter(BaseFilter):
    async def __call__(self, message: Message, state: FSMContext) -> bool:
        data = await state.get_data()
        if (
            data.get("supported_convert_formats")
            and data.get("file_id")
            and message.text.lower() in data["supported_convert_formats"]
        ):
            return {
                "file_id": data.get("file_id"),
                "file_name": data.get("file_name"),
                "file_type": data.get("file_type"),
                "output_type": message.text.lower(),
            }
        return False
