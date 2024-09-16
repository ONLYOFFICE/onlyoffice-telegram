from aiogram.filters import BaseFilter
from aiogram.types import Message

from app.utils.file_utils import get_format_by_mime


class DocumentEditFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if message.document:
            format = get_format_by_mime(message.document.mime_type)
            if "edit" in format["actions"]:
                return {"format": format}
        return False
