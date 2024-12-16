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

import logging
import uuid

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from redis import Redis

from app.filters import DocumentEditFilter
from app.fsm import MenuState
from app.keyboards import make_buttons, make_keyboard
from app.utils.file_utils import (
    remove_extension,
)
from app.utils.lang_utils import _, __
from config import BOT_NAME, MAX_FILE_SIZE_BYTES, TTL, WEB_APP_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()


@router.message(StateFilter(None), DocumentEditFilter())
async def handle_edit_no_command(
    message: Message, state: FSMContext, r: Redis, format, reply
):
    if reply:
        message = message.reply_to_message
    await handle_edit_document_upload(message, state, r, format)


@router.message(MenuState.on_start, F.text.lower() == __("open"))
async def handle_edit_start(message: Message, state: FSMContext):
    row_buttons = make_buttons([], with_back=True, with_cancel=True)
    keyboard = make_keyboard(row_buttons)
    await message.answer(
        text=_("Send file"),
        reply_markup=keyboard,
        reply_to_message_id=message.message_id,
    )
    await state.set_state(MenuState.on_edit_start)


@router.message(MenuState.on_edit_start, DocumentEditFilter())
async def handle_edit_document_upload(
    message: Message, state: FSMContext, r: Redis, format
):
    try:
        file = message.document
        if file.file_size > MAX_FILE_SIZE_BYTES:
            await message.answer(
                _("The file is too large. Maximum allowed file size is 20 MB"),
                reply_to_message_id=message.message_id,
            )

        key = uuid.uuid4().hex

        pipeline = r.pipeline()
        session = {
            "document_type": format["type"],
            "file_id": file.file_id,
            "file_name": remove_extension(file.file_name),
            "file_type": format["name"],
            "members": "",
            "message_id": message.message_id,
            "owner": message.from_user.id,
        }
        if message.chat.type == "group":
            session["group"] = message.chat.id
        pipeline.hset(key, mapping=session)
        pipeline.expire(key, TTL)
        pipeline.execute()

        web_app_url = f"https://t.me/{BOT_NAME}/{WEB_APP_NAME}?startapp={key}"

        edit_mode = True if "edit" in format["actions"] else False
        text_message = (
            _("To start co-editing, send this message to other participants")
            if edit_mode
            else _("To start co-viewing, send this message to other participants")
        )

        await state.clear()
        await message.answer(
            text=_("Your file {file_name}\n{text_message}\n{web_app_url}").format(
                file_name=file.file_name, text_message=text_message, web_app_url=web_app_url
            ),
            reply_markup=ReplyKeyboardRemove(),
            reply_to_message_id=message.message_id,
        )

    except Exception as e:
        logger.error(f"Failed to create web app link: {e}")
