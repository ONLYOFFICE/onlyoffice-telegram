from aiogram.filters import BaseFilter
from aiogram.types import Message

from app.utils.file_utils import get_all_mime


class DocumentTypeFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if message.document:
            mime_types = get_all_mime()
            return message.document.mime_type in mime_types
        return False
