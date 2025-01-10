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
