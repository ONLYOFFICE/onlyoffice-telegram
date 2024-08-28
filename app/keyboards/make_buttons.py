from aiogram.types import KeyboardButton

from app.utils.lang_utils import _


def make_buttons(
    items: list[str],
    buttons_per_row: int = 4,
    with_back: bool = False,
    with_cancel: bool = False,
) -> list[list[KeyboardButton]]:
    rows = [
        items[i : i + buttons_per_row] for i in range(0, len(items), buttons_per_row)
    ]

    row_buttons = [[KeyboardButton(text=item) for item in row] for row in rows]

    if with_back:
        row_buttons.append([KeyboardButton(text=_("Back"))])

    if with_cancel:
        row_buttons.append([KeyboardButton(text=_("Cancel"))])

    return row_buttons
