import logging
import uuid

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import LinkPreviewOptions, Message, ReplyKeyboardRemove
from redis import Redis

from app.filters import DocumentNameFilter
from app.fsm import MenuState
from app.keyboards import make_buttons, make_keyboard
from app.utils.file_utils import (
    get_document_type_by_format,
    get_file_type_by_format,
)
from app.utils.lang_utils import _, __
from config import BOT_NAME, TTL, WEB_APP_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()


@router.message(MenuState.on_start, F.text.lower() == __("create"))
async def handle_create_start(message: Message, state: FSMContext):
    menu_items = ["Document", "Spreadsheet", "Presentation", "Form"]
    row_buttons = make_buttons(menu_items, with_back=True, with_cancel=True)
    keyboard = make_keyboard(row_buttons)
    await message.answer(text=_("Select document format"), reply_markup=keyboard)
    await state.set_state(MenuState.on_create_start)


@router.message(MenuState.on_create_start, F.text)
async def handle_create_title(message: Message, state: FSMContext):
    format = message.text.lower()
    if format in ["document", "spreadsheet", "presentation", "form"]:
        await state.update_data(format=format)
        await message.answer(
            text=_("Enter document title"), reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(MenuState.on_create_title)
    else:
        await handle_create_start(message, state)


@router.message(MenuState.on_create_title, DocumentNameFilter())
async def handle_create_document(message: Message, state: FSMContext, r: Redis):
    file_name = message.text
    data = await state.get_data()
    format = data["format"]
    if format.lower() in ["document", "spreadsheet", "presentation", "form"]:
        try:
            key = uuid.uuid4().hex

            pipeline = r.pipeline()
            config_data = {
                "file_name": file_name,
                "document_type": get_document_type_by_format(format),
                "file_type": get_file_type_by_format(format),
                "members": "",
            }
            if message.chat.type == "group":
                config_data["group"] = message.chat.id
            pipeline.hset(key, mapping=config_data)
            pipeline.expire(key, TTL)
            pipeline.execute()

            web_app_url = f"https://t.me/{BOT_NAME}/{WEB_APP_NAME}?startapp={key}"
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
    else:
        await handle_create_start(message, state)


@router.message(MenuState.on_create_title, F.text)
async def handle_edit_invalid_document_upload(message: Message):
    await message.answer(_("Invalid title"))
