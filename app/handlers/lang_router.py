from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from redis import Redis

from app.keyboards import LangCallback, make_lang_buttons
from app.utils.lang_utils import _

router = Router()


@router.message(Command("lang"))
async def handle_lang(message: Message, state: FSMContext):
    # TODO: Remove the keyboard if it is open
    await state.clear()
    await message.answer(text=_("Select language"), reply_markup=make_lang_buttons())


@router.callback_query(LangCallback.filter())
async def lang_callback(call: CallbackQuery, r: Redis, callback_data: LangCallback):
    key = f"{call.message.chat.id}:lang"
    r.set(key, callback_data.lang)

    await call.message.edit_text(
        _("Language changed", locale=callback_data.lang), reply_markup=None
    )
