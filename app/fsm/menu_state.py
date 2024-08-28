from aiogram.fsm.state import State, StatesGroup


class MenuState(StatesGroup):
    on_start = State()
    on_create_start = State()
    on_create_title = State()
    on_convert_start = State()
    on_convert_format_selection = State()
    on_edit_start = State()
    on_edit_single_mode = State()
    on_edit_coop_mode = State()
