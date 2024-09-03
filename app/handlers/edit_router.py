import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import LinkPreviewOptions, Message, ReplyKeyboardRemove
from redis import Redis

from app.filters import DocumentTypeFilter
from app.fsm import MenuState
from app.keyboards import make_buttons, make_keyboard
from app.utils.file_utils import get_document_type, get_file_type
from app.utils.lang_utils import _, __
from config import BOT_NAME, MAX_FILE_SIZE_BYTES, TTL, WEB_APP_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()


@router.message(MenuState.on_start, F.text.lower() == __("edit"))
async def handle_edit_start(message: Message, state: FSMContext):
    row_buttons = make_buttons([], with_back=True, with_cancel=True)
    keyboard = make_keyboard(row_buttons)
    await message.answer(text=_("Send file"), reply_markup=keyboard)
    await state.set_state(MenuState.on_edit_start)


@router.message(MenuState.on_edit_start, DocumentTypeFilter())
async def handle_edit_document_upload(message: Message, state: FSMContext, r: Redis):
    try:
        file = message.document
        if file.file_size > MAX_FILE_SIZE_BYTES:
            await message.answer(
                _("The file is too large. Maximum allowed file size is 20 MB")
            )

        key = f"{message.chat.id}:{file.file_unique_id}"

        pipeline = r.pipeline()
        config_data = {
            "file_id": file.file_id,
            "file_unique_id": file.file_unique_id,
            "file_name": file.file_name,
            "document_type": get_document_type(file.file_name),
            "file_type": get_file_type(file.file_name),
            "chat_id": message.chat.id,
            "message_id": message.message_id,
        }
        pipeline.hset(f"{key}:config", mapping=config_data)
        pipeline.expire(f"{key}:config", TTL)
        pipeline.execute()

        web_app_url = f"https://t.me/{BOT_NAME}/{WEB_APP_NAME}?startapp={message.chat.id}_{file.file_unique_id}"
        link_preview_options = LinkPreviewOptions(url=web_app_url)

        await state.clear()
        await message.answer(
            text=_(
                "For co-editing, send this message to other participants\n{web_app_url}"
            ).format(web_app_url=web_app_url),
            link_preview_options=link_preview_options,
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
