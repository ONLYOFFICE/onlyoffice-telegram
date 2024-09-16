from aiogram import Dispatcher

from .back_router import router as back_router
from .cancel_router import router as cancel_router
from .convert_router import router as convert_router
from .create_router import router as create_router
from .edit_router import router as edit_router
from .lang_router import router as lang_router
from .start_router import router as start_router


def setup_handlers(dispatcher: Dispatcher) -> None:
    # The order in which routers are connected is important
    dispatcher.include_routers(
        back_router,
        cancel_router,
        lang_router,
        convert_router,
        create_router,
        edit_router,
        start_router,
    )
