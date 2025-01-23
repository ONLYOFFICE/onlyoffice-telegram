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

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from redis import Redis

from app.keyboards import LangCallback, make_lang_buttons
from app.utils.lang_utils import _

router = Router()


@router.message(F.chat.type == "private", Command("lang"))
async def handle_lang(message: Message, state: FSMContext):
    await state.clear()
    # Keyboard removal is only available when sending a message with reply_markup, so we're sending two messages
    await message.answer(
        text=_("Select language"),
        reply_markup=ReplyKeyboardRemove(selective=True),
        reply_to_message_id=message.message_id,
    )
    await message.answer(
        text=_("Available languages:"),
        reply_markup=make_lang_buttons(message.from_user.id),
    )


@router.callback_query(LangCallback.filter())
async def lang_callback(call: CallbackQuery, r: Redis, callback_data: LangCallback):
    if call.from_user and call.from_user.id == callback_data.user_id:
        key = f"{callback_data.user_id}:lang"
        r.set(key, callback_data.lang)

        await call.message.edit_text(_("Language changed", locale=callback_data.lang), reply_markup=None)
