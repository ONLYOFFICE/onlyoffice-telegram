import asyncio
import logging
import uuid

import aiohttp
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, URLInputFile
from redis import Redis

from app.filters import SupportedConvertFormatsFilter
from app.fsm import MenuState
from app.keyboards import make_buttons, make_keyboard
from app.utils.file_utils import get_extension_by_name, get_format_by_mime
from app.utils.jwt_utils import encode_payload
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
    await message.answer(text=_("Send file"), reply_markup=keyboard)
    await state.set_state(MenuState.on_convert_start)


@router.message(MenuState.on_convert_start, F.photo)
async def handle_conversion_photo_upload(message: Message):
    await message.answer(_("File not supported"))


@router.message(MenuState.on_convert_start, F.document)
async def handle_conversion_document_upload(message: Message, state: FSMContext):
    file = message.document
    file_size = file.file_size

    if file_size > MAX_FILE_SIZE_BYTES:
        await message.answer(
            _("The file is too large. Maximum allowed file size is 20 MB")
        )
        return

    format = get_format_by_mime(file.mime_type)
    if format and format["convert"]:
        await state.update_data(
            file_id=file.file_id,
            file_name=file.file_name,
            file_type=get_extension_by_name(file.file_name),
            supported_convert_formats=format["convert"],
        )
        row_buttons = make_buttons(
            [item.upper() for item in format["convert"]],
            buttons_per_row=4,
            separate=True,
            with_back=True,
            with_cancel=True,
        )
        keyboard = make_keyboard(row_buttons)
        await message.answer(text=_("Select format to convert"), reply_markup=keyboard)
        await state.set_state(MenuState.on_convert_format_selection)
    else:
        await message.answer(_("File not supported"))


@router.message(MenuState.on_convert_start)
async def handle_conversion_no_file(message: Message, state: FSMContext):
    await handle_conversion_start(message, state)


async def check_conversion_status(session: aiohttp.ClientSession, key: str) -> dict:
    url = f"{WEB_APP_URL}/editor/getFile?file_id={key}"
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.json()


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
    key = uuid.uuid4().hex
    conversion_url = f"{DOCSERVER_URL}/{DOCSERVER_CONVERTER_URL}"
    payload = {
        "async": "true",
        "url": f"{WEB_APP_URL}/editor/getFile?key={key}",
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
                async with session.post(
                    conversion_url, json=payload, headers=headers
                ) as response:
                    if response.status != 200:
                        raise RuntimeError(
                            f"Conversion service returned status: {response.status}"
                        )
                    try:
                        conversion_response = await response.json()
                    except aiohttp.ContentTypeError:
                        raise RuntimeError("Failed to parse response as JSON")

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
            filename=f"{file_name}.{output_type}",
        )
        await bot.send_document(
            chat_id=message.from_user.id,
            document=document,
            caption=_("Done"),
            reply_markup=ReplyKeyboardRemove(),
        )
    else:
        await message.answer(
            _("Failed to convert file"), reply_markup=ReplyKeyboardRemove()
        )


@router.message(MenuState.on_convert_format_selection)
async def handle_conversion_invalid_format_selection(message: Message):
    await message.answer(_("Invalid format"))
