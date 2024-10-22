import logging
import uuid

from aiogram import F, Router
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


@router.message(MenuState.on_start, F.text.lower() == __("open"))
async def handle_edit_start(message: Message, state: FSMContext):
    row_buttons = make_buttons([], with_back=True, with_cancel=True)
    keyboard = make_keyboard(row_buttons)
    await message.answer(text=_("Send file"), reply_markup=keyboard)
    await state.set_state(MenuState.on_edit_start)


@router.message(MenuState.on_edit_start, DocumentEditFilter())
async def handle_edit_document_upload(
    message: Message, state: FSMContext, r: Redis, format
):
    try:
        file = message.document
        if file.file_size > MAX_FILE_SIZE_BYTES:
            await message.answer(
                _("The file is too large. Maximum allowed file size is 20 MB")
            )

        key = uuid.uuid4().hex

        pipeline = r.pipeline()
        session = {
            "document_type": format["type"],
            "file_id": file.file_id,
            "file_name": remove_extension(file.file_name),
            "file_type": format["name"],
            "members": "",
        }
        if message.chat.type == "group":
            session["group"] = message.chat.id
        pipeline.hset(key, mapping=session)
        pipeline.expire(key, TTL)
        pipeline.execute()

        web_app_url = f"https://t.me/{BOT_NAME}/{WEB_APP_NAME}?startapp={key}"

        await state.clear()
        await message.answer(
            text=_(
                "To start co-editing, send this message to other participants\n{web_app_url}"
            ).format(web_app_url=web_app_url),
            reply_markup=ReplyKeyboardRemove(),
        )

    except Exception as e:
        logger.error(f"Failed to create web app link: {e}")


@router.message(MenuState.on_edit_start, F.document)
async def handle_edit_invalid_document_upload(message: Message):
    await message.answer(_("File not supported"))


@router.message(MenuState.on_edit_start)
async def handle_edit_no_file(message: Message, state: FSMContext):
    await handle_edit_start(message, state)
