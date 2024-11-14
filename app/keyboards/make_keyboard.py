from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def make_keyboard(keyboard: list[list[KeyboardButton]]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, is_persistent=True)
