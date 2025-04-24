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

import logging
import re
import uuid

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from redis import Redis

from app.filters import ChatGroupFilter, DocumentEditFilter, NotCommandFilter
from app.fsm import MenuState
from app.utils.file_utils import (
    remove_extension,
)
from app.utils.lang_utils import _, __
from config import BOT_NAME, MAX_FILE_SIZE_BYTES, TTL, WEB_APP_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()


@router.message(StateFilter(None), F.chat.type == "private", DocumentEditFilter())
async def handle_edit_no_command(message: Message, state: FSMContext, r: Redis, f, reply):
    await handle_edit_document_upload(message, state, r, f, reply)


@router.message(ChatGroupFilter(), Command("open"), DocumentEditFilter())
@router.message(ChatGroupFilter(), DocumentEditFilter())
async def handle_edit_file_group(message: Message, state: FSMContext, r: Redis, f, reply):
    await state.clear()
    await handle_edit_document_upload(message, state, r, f, reply)


@router.message(ChatGroupFilter(), Command("open"))
async def handle_edit_group(message: Message, state: FSMContext):
    await state.clear()
    await handle_edit_start(message, state)


@router.message(MenuState.on_start, F.text.lower() == __("open"))
async def handle_edit_start(message: Message, state: FSMContext):
    await message.answer(
        text=_("Send file"),
        reply_markup=ReplyKeyboardRemove(selective=True),
        reply_to_message_id=message.message_id,
    )
    await state.set_state(MenuState.on_edit_start)


@router.message(MenuState.on_edit_start, DocumentEditFilter())
async def handle_edit_document_upload(message: Message, state: FSMContext, r: Redis, f, reply: bool):
    try:
        lang = None
        pipeline = r.pipeline()
        pipeline.get(f"{message.chat.id}:lang")
        pipeline.get(f"{message.from_user.id}:lang")
        results = pipeline.execute()
        if results[0]:
            lang = results[0].decode("utf-8")
        elif results[1]:
            lang = results[1].decode("utf-8")
        else:
            lang = getattr(message.from_user, "language_code", "default") or "default"

        if reply:
            message = message.reply_to_message
        file = message.document
        if file.file_size > MAX_FILE_SIZE_BYTES:
            await message.answer(
                _("The file is too large. Maximum allowed file size is 20 MB"),
                reply_to_message_id=message.message_id,
            )
            return

        session = {
            "document_type": f["type"],
            "file_id": file.file_id,
            "file_name": remove_extension(file.file_name),
            "file_type": f["name"],
            "lang": lang,
            "members": "",
            "message_id": message.message_id,
            "owner": message.chat.id,
        }
        if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            session["group"] = message.chat.id

        key = uuid.uuid4().hex
        web_app_url = f"https://t.me/{BOT_NAME}/{WEB_APP_NAME}?startapp={key}"

        edit_mode = True if "edit" in f["actions"] else False
        edit_messages = {"01": _("Your file"), "03": _("The ONLYOFFICE editor link:")}
        if edit_mode:
            if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
                edit_messages["02"] = _("All group members can edit this file.")
            else:
                edit_messages["02"] = _("To start co-editing, send this message to other participants.")
        else:
            if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
                edit_messages["02"] = _("All group members can view this file. The link is available for 24 hours.")
            else:
                edit_messages["02"] = _(
                    "To open the file for viewing by several users, send this message to other participants. The link is available for 24 hours."  # pylint: disable=line-too-long
                )

        await state.clear()
        file_name = re.sub(r"\.(?!.*\.)", "\u200b.", file.file_name)
        link_message = await message.answer(
            text=f"{edit_messages['01']} <b>{file_name}</b>\n{edit_messages['02']}\n\n{edit_messages['03']}\n{web_app_url}",
            reply_to_message_id=message.message_id,
        )
        session["link_message_id"] = link_message.message_id

        pipeline = r.pipeline()
        pipeline.hset(key, mapping=session)
        pipeline.expire(key, TTL)
        pipeline.execute()

    except Exception as e:
        logger.error(f"Failed to create web app link: {e}")


@router.message(MenuState.on_edit_start, NotCommandFilter())
async def handle_edit_no_file(message: Message, state: FSMContext):
    await handle_edit_start(message, state)
