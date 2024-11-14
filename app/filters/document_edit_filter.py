from aiogram.filters import BaseFilter
from aiogram.types import Message

from app.utils.file_utils import get_format_by_mime
from app.utils.lang_utils import _


class DocumentEditFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        async def process_message(reply=False) -> bool:
            if message.chat.type != "private":
                return False

            if message.document:
                format = get_format_by_mime(message.document.mime_type)
                if format and format["actions"]:
                    return {"format": format, "reply": reply}
                return await message.answer(_("File not supported"))

            if message.photo:
                return await message.answer(_("File not supported"))

            return False

        result = await process_message()
        if result:
            return result

        if message.reply_to_message:
            message = message.reply_to_message
            return await process_message(reply=True)

        return False
