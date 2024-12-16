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

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.fsm import MenuState
from app.handlers.convert_router import handle_conversion_start
from app.handlers.create_router import handle_create_start
from app.handlers.start_router import handle_start
from app.utils.lang_utils import __

router = Router()


@router.message(F.text.lower() == __("⬅️ back"))
async def handle_back_button(message: Message, state: FSMContext):
    current_state = await state.get_state()

    # For create
    if current_state == MenuState.on_create_start.state:
        await handle_start(message, state)
    if current_state == MenuState.on_create_title.state:
        await handle_create_start(message, state)

    # For convert
    if current_state == MenuState.on_convert_start.state:
        await handle_start(message, state)
    if current_state == MenuState.on_convert_format_selection.state:
        await handle_conversion_start(message, state)

    # For edit
    if current_state == MenuState.on_edit_start.state:
        await handle_start(message, state)
