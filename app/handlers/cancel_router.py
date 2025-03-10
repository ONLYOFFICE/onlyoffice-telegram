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
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from app.filters import ChatGroupFilter
from app.utils.lang_utils import _, __

router = Router()


@router.message(F.chat.type == "private", StateFilter(None), Command(commands=["cancel"]))
@router.message(F.chat.type == "private", StateFilter(None), F.text.lower() == __("❌ cancel"))
async def cmd_cancel_no_state(message: Message, state: FSMContext):
    await state.set_data({})
    await message.answer(
        text=_("There is nothing to cancel"),
        reply_markup=ReplyKeyboardRemove(selective=True),
        reply_to_message_id=message.message_id,
    )


@router.message(F.chat.type == "private", Command(commands=["cancel"]))
@router.message(F.chat.type == "private", F.text.lower() == __("❌ cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        text=_("Action canceled"),
        reply_markup=ReplyKeyboardRemove(selective=True),
        reply_to_message_id=message.message_id,
    )


@router.message(ChatGroupFilter(), StateFilter(None), Command(commands=["cancel"]))
async def cmd_cancel_no_state_group():
    return


@router.message(ChatGroupFilter(), Command(commands=["cancel"]))
async def cmd_cancel_group(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        text=_("Action canceled"),
        reply_markup=ReplyKeyboardRemove(selective=True),
        reply_to_message_id=message.message_id,
    )
