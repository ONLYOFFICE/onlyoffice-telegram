from aiogram import Bot

from app.utils.lang_utils import _, i18n


async def set_description(bot: Bot):
    for lang in i18n.available_locales:
        await bot.set_my_description(
            _(
                "📑 ONLYOFFICE bot can create, open and convert office files\n\n- Create documents, spreadsheets, presentations, PDF forms\n- Open your local files and edit them\n- Collaborate with other people in real time\n- Convert files to multiple formats\n\nPress /start to create/edit files\n",
                locale=lang,
            ),
            language_code=lang,
        )
        await bot.set_my_short_description(
            _(
                "Easily create, convert, edit and collaborate on office files using the ONLYOFFICE bot.",
                locale=lang,
            ),
            language_code=lang,
        )
