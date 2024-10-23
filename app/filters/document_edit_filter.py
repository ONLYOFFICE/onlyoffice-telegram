from aiogram.filters import BaseFilter
from aiogram.types import Message

from app.utils.file_utils import get_format_by_mime
from app.utils.lang_utils import _


class DocumentEditFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if message.document:
            format = get_format_by_mime(message.document.mime_type)
            if format and "edit" in format["actions"]:
                return {"format": format}
            else:
                return await message.answer(_("File not supported"))
        elif message.photo:
            return await message.answer(_("File not supported"))
        return False
