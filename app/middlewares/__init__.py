from aiogram import Dispatcher

from .lang import i18n_middleware


def setup_middlewares(dp: Dispatcher) -> None:
    dp.update.middleware(i18n_middleware)
