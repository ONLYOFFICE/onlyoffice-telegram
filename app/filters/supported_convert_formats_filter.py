from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message


class SupportedConvertFormatsFilter(BaseFilter):
    async def __call__(self, message: Message, state: FSMContext) -> bool:
        data = await state.get_data()
        if (
            data.get("supported_convert_formats")
            and data.get("file_id")
            and message.text.lower() in data["supported_convert_formats"]
        ):
            return {
                "file_id": data.get("file_id"),
                "file_name": data.get("file_name"),
                "file_type": data.get("file_type"),
                "output_type": message.text.lower(),
            }
        return False
