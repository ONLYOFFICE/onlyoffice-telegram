#
# (c) Copyright Ascensio System SIA 2025
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

from .antiflood import throttling_middleware
from .lang import i18n_middleware


def setup_middlewares(dp: Dispatcher) -> None:
    # throttling_middleware runs first to filter out messages that do not need a lang definition
    dp.update.middleware(throttling_middleware)
    dp.update.middleware(i18n_middleware)
