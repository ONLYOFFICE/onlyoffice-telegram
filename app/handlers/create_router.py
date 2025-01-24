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
import uuid

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from redis import Redis

from app.filters import ChatGroupFilter, DocumentNameFilter, NotCommandFilter
from app.fsm import MenuState
from app.keyboards import make_buttons, make_keyboard
from app.utils.file_utils import (
    get_extension_by_description,
    get_format_by_extension,
    get_format_descriptions,
)
from app.utils.lang_utils import _, __
from config import BOT_NAME, TTL, WEB_APP_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()


@router.message(MenuState.on_start, F.text.lower() == __("create"))
async def handle_create_start(message: Message, state: FSMContext):
    menu_items = get_format_descriptions()
    row_buttons = make_buttons(menu_items, with_back=True, with_cancel=True)
    keyboard = make_keyboard(row_buttons)
    await message.answer(
        text=_("Select file format"),
        reply_markup=keyboard,
        reply_to_message_id=message.message_id,
    )
    await state.set_state(MenuState.on_create_start)


@router.message(ChatGroupFilter(), Command("document"))
@router.message(ChatGroupFilter(), Command("spreadsheet"))
@router.message(ChatGroupFilter(), Command("presentation"))
async def handle_create_group(message: Message, state: FSMContext, command: CommandObject):
    await state.clear()
    await state.update_data(format_description=_(command.command.capitalize()))
    await message.answer(
        text=_("Enter file title"),
        reply_markup=ReplyKeyboardRemove(selective=True),
        reply_to_message_id=message.message_id,
    )
    await state.set_state(MenuState.on_create_title)


@router.message(MenuState.on_create_start, F.text, NotCommandFilter())
async def handle_create_title(message: Message, state: FSMContext):
    if any(
        message.text.casefold() == format_description.casefold() for format_description in get_format_descriptions()
    ):
        await state.update_data(format_description=message.text)
        await message.answer(
            text=_("Enter file title"),
            reply_markup=ReplyKeyboardRemove(selective=True),
            reply_to_message_id=message.message_id,
        )
        await state.set_state(MenuState.on_create_title)
    else:
        await handle_create_start(message, state)


@router.message(MenuState.on_create_title, DocumentNameFilter())
async def handle_create_document(message: Message, state: FSMContext, r: Redis):
    file_name = message.text
    data = await state.get_data()
    format_description = data["format_description"]
    extension = get_extension_by_description(format_description)
    f = get_format_by_extension(extension)
    try:
        lang = r.get(f"{message.chat.id}:lang")
        if not lang:
            lang = getattr(message.from_user, "language_code", "default") or "default"
        else:
            lang = lang.decode("utf-8")

        key = uuid.uuid4().hex

        pipeline = r.pipeline()
        session = {
            "document_type": f["type"],
            "file_name": file_name,
            "file_type": f["name"],
            "lang": lang,
            "members": "",
            "message_id": message.message_id,
            "owner": message.chat.id,
        }
        if message.chat.type == "group" or message.chat.type == "supergroup":
            session["group"] = message.chat.id

        web_app_url = f"https://t.me/{BOT_NAME}/{WEB_APP_NAME}?startapp={key}"

        create_messages = {
            "01": _("Your file"),
            "02": _("To start co-editing, send this message to other participants."),
            "03": _("The ONLYOFFICE editor link:"),
        }

        await state.clear()
        link_message = await message.answer(
            text=f"{create_messages['01']} <b>{file_name}.{f['name']}</b>\n{create_messages['02']}\n\n{create_messages['03']}\n{web_app_url}",  # pylint: disable=line-too-long
            reply_to_message_id=message.message_id,
        )
        session["link_message_id"] = link_message.message_id

        pipeline.hset(key, mapping=session)
        pipeline.expire(key, TTL)
        pipeline.execute()

    except Exception as e:
        logger.error(f"Failed to create web app link: {e}")


@router.message(MenuState.on_create_title, F.text, NotCommandFilter())
async def handle_edit_invalid_document_upload(message: Message):
    await message.answer(_("Invalid title"), reply_to_message_id=message.message_id)
