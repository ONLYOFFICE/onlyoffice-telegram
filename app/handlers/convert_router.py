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

import asyncio
import logging
import uuid

import aiohttp
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, URLInputFile
from redis import Redis

from app.filters import NotCommandFilter, SupportedConvertFormatsFilter
from app.fsm import MenuState
from app.keyboards import make_buttons, make_keyboard
from app.utils.file_utils import (
    get_extension_by_name,
    get_format_by_extension,
    remove_extension,
)
from app.utils.jwt_utils import create_token, encode_payload
from app.utils.lang_utils import _, __
from config import (
    CONVERT_MAX_ATTEMPTS,
    CONVERT_TIMEOUT,
    DOCSERVER_CONVERTER_URL,
    DOCSERVER_URL,
    JWT_HEADER,
    MAX_FILE_SIZE_BYTES,
    TTL,
    WEB_APP_URL,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()


@router.message(MenuState.on_start, F.text.lower() == __("🔄 convert"))
async def handle_conversion_start(message: Message, state: FSMContext):
    row_buttons = make_buttons([], with_back=True, with_cancel=True)
    keyboard = make_keyboard(row_buttons)
    await message.answer(
        text=_("Send file"),
        reply_markup=keyboard,
        reply_to_message_id=message.message_id,
    )
    await state.set_state(MenuState.on_convert_start)


@router.message(MenuState.on_convert_start, F.photo)
async def handle_conversion_photo_upload(message: Message):
    await message.answer(_("File not supported"), reply_to_message_id=message.message_id)


@router.message(MenuState.on_convert_start, F.document)
async def handle_conversion_document_upload(message: Message, state: FSMContext):
    file = message.document
    file_size = file.file_size

    if file_size > MAX_FILE_SIZE_BYTES:
        await message.answer(
            _("The file is too large. Maximum allowed file size is 20 MB"),
            reply_to_message_id=message.message_id,
        )
        return

    extension = get_extension_by_name(file.file_name)
    f = get_format_by_extension(extension)
    if f and f["convert"]:
        await state.update_data(
            file_id=file.file_id,
            file_name=file.file_name,
            file_type=extension,
            supported_convert_formats=f["convert"],
        )
        row_buttons = make_buttons(
            [item.upper() for item in f["convert"]],
            buttons_per_row=4,
            separate=True,
            with_back=True,
            with_cancel=True,
        )
        keyboard = make_keyboard(row_buttons)
        await message.answer(
            text=_("Select format to convert"),
            reply_markup=keyboard,
            reply_to_message_id=message.message_id,
        )
        await state.set_state(MenuState.on_convert_format_selection)
    else:
        await message.answer(text=_("File not supported"), reply_to_message_id=message.message_id)


@router.message(MenuState.on_convert_start, NotCommandFilter())
async def handle_conversion_no_file(message: Message, state: FSMContext):
    await handle_conversion_start(message, state)


@router.message(MenuState.on_convert_format_selection, SupportedConvertFormatsFilter())
async def handle_conversion_finish(
    message: Message,
    bot: Bot,
    r: Redis,
    state: FSMContext,
    file_id: str,
    file_name: str,
    file_type: str,
    output_type: str,
):
    msg = await message.answer(
        _("🔄 Conversion..."),
        reply_markup=ReplyKeyboardRemove(selective=True),
        reply_to_message_id=message.message_id,
    )

    key = uuid.uuid4().hex
    security_token = create_token(key)
    conversion_url = f"{DOCSERVER_URL}/{DOCSERVER_CONVERTER_URL}"
    payload = {
        "async": "true",
        "url": f"{WEB_APP_URL}/editor/getFile?security_token={security_token}",
        "key": f"{uuid.uuid4().hex}",
        "title": file_name,
        "filetype": file_type,
        "outputtype": output_type,
    }
    headers = {"accept": "application/json"}
    token = encode_payload(payload)
    payload["token"] = token
    headers[JWT_HEADER] = f"Bearer {token}"

    r.hset(
        key,
        mapping={
            "file_id": file_id,
            "file_type": file_type,
        },
    )
    r.expire(key, TTL)

    async with aiohttp.ClientSession() as session:
        end_convert = False
        for attempt in range(CONVERT_MAX_ATTEMPTS):
            try:
                async with session.post(conversion_url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        raise RuntimeError(f"Conversion service returned status: {response.status}")
                    try:
                        conversion_response = await response.json()
                    except aiohttp.ContentTypeError as e:
                        raise RuntimeError("Failed to parse response as JSON") from e

                    end_convert = conversion_response.get("endConvert", False)
                    if end_convert:
                        break
                    await asyncio.sleep(CONVERT_TIMEOUT)
            except RuntimeError as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")

    await state.clear()
    if end_convert:
        document = URLInputFile(
            conversion_response.get("fileUrl"),
            filename=f"{remove_extension(file_name)}.{output_type}",
        )
        await msg.delete()
        await bot.send_document(
            chat_id=message.chat.id,
            document=document,
            caption=_("Your file is ready. Please find the final version here."),
            reply_to_message_id=message.message_id,
        )
    else:
        await msg.delete()
        await message.answer(_("Failed to convert file"), reply_to_message_id=message.message_id)


@router.message(MenuState.on_convert_format_selection, NotCommandFilter())
async def handle_conversion_invalid_format_selection(message: Message):
    await message.answer(_("Invalid format"), reply_to_message_id=message.message_id)
