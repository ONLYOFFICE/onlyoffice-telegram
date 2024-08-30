from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from redis import Redis

from app.keyboards import LangCallback, make_lang_buttons
from app.utils.lang_utils import _

router = Router()


@router.message(Command("lang"))
async def handle_lang(message: Message, state: FSMContext):
    await state.clear()
    # Keyboard removal is only available when sending a message with reply_markup, so we're sending two messages
    await message.answer(text=_("Select language"), reply_markup=ReplyKeyboardRemove())
    await message.answer(
        text=_("Available languages:"), reply_markup=make_lang_buttons()
    )


@router.callback_query(LangCallback.filter())
async def lang_callback(call: CallbackQuery, r: Redis, callback_data: LangCallback):
    key = f"{call.message.chat.id}:lang"
    r.set(key, callback_data.lang)

    await call.message.edit_text(
        _("Language changed", locale=callback_data.lang), reply_markup=None
    )
