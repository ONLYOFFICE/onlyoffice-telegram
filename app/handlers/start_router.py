from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.fsm import MenuState
from app.keyboards import make_buttons, make_keyboard
from app.utils.lang_utils import _

router = Router()


@router.message(Command("start"))
async def handle_start(message: Message, state: FSMContext):
    menu_items = [_("Create"), _("Open"), _("🔄 Convert")]
    await state.clear()
    row_buttons = make_buttons(menu_items, with_cancel=True)
    keyboard = make_keyboard(row_buttons)
    await message.answer(text=_("Choose an action"), reply_markup=keyboard)
    await state.set_state(MenuState.on_start)
