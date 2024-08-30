from aiogram import Dispatcher

from .antiflood import throttling_middleware
from .lang import i18n_middleware


def setup_middlewares(dp: Dispatcher) -> None:
    dp.update.middleware(i18n_middleware)
    dp.update.middleware(throttling_middleware)
