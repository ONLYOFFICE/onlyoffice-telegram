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

from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.types import Message

from app.utils.lang_utils import _

router = Router()


@router.message(StateFilter(None), Command("help"))
async def handle_help(message: Message):
    await message.answer(
        text=_(
            "📑 ONLYOFFICE bot can create, open and convert office files\n\n- Create documents, spreadsheets, presentations\n- Open your local files and edit them\n- Collaborate with other people in real time\n- Convert files to multiple formats\n\nPress /start to get started and see the available options:\n☑️ Click the Create button to create new files and send them to other Telegram users for co-editing.\n☑️ Click the Open button to upload and open files from your device.\n☑️ Click the Convert button to select files for conversion."
        )
    )
