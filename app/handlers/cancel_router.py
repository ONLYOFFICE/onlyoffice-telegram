from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from app.utils.lang_utils import _, __

router = Router()


@router.message(StateFilter(None), Command(commands=["cancel"]))
@router.message(StateFilter(None), F.text.lower() == __("❌ cancel"))
async def cmd_cancel_no_state(message: Message, state: FSMContext):
    await state.set_data({})
    await message.answer(
        text=_("There is nothing to cancel"), reply_markup=ReplyKeyboardRemove()
    )


@router.message(Command(commands=["cancel"]))
@router.message(F.text.lower() == __("❌ cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(text=_("Action canceled"), reply_markup=ReplyKeyboardRemove())
