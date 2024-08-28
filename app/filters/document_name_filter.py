import re

from aiogram.filters import BaseFilter
from aiogram.types import Message


class DocumentNameFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        forbidden_chars = r'[<>:"/\\|?*]'
        if message.text:
            if re.search(forbidden_chars, message.text):
                return False
            return True
        return False
