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

from aiogram.types import KeyboardButton

from app.utils.lang_utils import _


def make_buttons(
    items: list[str],
    buttons_per_row: int = 2,
    separate: bool = False,
    with_back: bool = False,
    with_cancel: bool = False,
) -> list[list[KeyboardButton]]:
    if not separate:
        if with_back:
            items.append(_("⬅️ Back"))
        if with_cancel:
            items.append(_("❌ Cancel"))
        rows = [
            items[i : i + buttons_per_row]
            for i in range(0, len(items), buttons_per_row)
        ]
    else:
        rows = [
            items[i : i + buttons_per_row]
            for i in range(0, len(items), buttons_per_row)
        ]
        function_buttons = []
        if with_back:
            function_buttons.append(_("⬅️ Back"))
        if with_cancel:
            function_buttons.append(_("❌ Cancel"))
        rows.append(function_buttons)

    row_buttons = [[KeyboardButton(text=item) for item in row] for row in rows]

    return row_buttons
