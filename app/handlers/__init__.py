#
# (c) Copyright Ascensio System SIA 2024
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from aiogram import Dispatcher

from .back_router import router as back_router
from .cancel_router import router as cancel_router
from .convert_router import router as convert_router
from .create_router import router as create_router
from .edit_router import router as edit_router
from .help_router import router as help_router
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
        help_router,
        start_router,
    )
