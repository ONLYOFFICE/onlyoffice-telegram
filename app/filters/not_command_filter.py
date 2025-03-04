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

from aiogram.filters import BaseFilter
from aiogram.types import Message

from app.commands import get_group_chats_commands, get_private_chats_commands
from config import BOT_NAME


class NotCommandFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if message.chat.type == "private":
            private_chats_commands = get_private_chats_commands()
            for bot_command in private_chats_commands:
                if bot_command.command == message.text:
                    return False
        if message.chat.type == "group" or message.chat.type == "supergroup":
            group_chats_commands = get_group_chats_commands()
            for bot_command in group_chats_commands:
                if f"{bot_command.command}@{BOT_NAME}" == message.text:
                    return False
        return True
