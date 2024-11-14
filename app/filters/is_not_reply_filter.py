from aiogram.filters import BaseFilter
from aiogram.types import Message


class IsNotReplyFilter(BaseFilter):
    async def __call__(self, msg: Message):
        if msg.reply_to_message:
            return False
        return True
