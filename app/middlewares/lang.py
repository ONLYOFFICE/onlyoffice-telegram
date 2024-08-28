from aiogram.types import Update
from aiogram.utils.i18n import I18nMiddleware
from redis import Redis

from app.utils.lang_utils import i18n


class SimpleI18nMiddleware(I18nMiddleware):
    async def get_locale(self, event: Update, data: dict) -> str:
        r: Redis = data["r"]

        from_user = None
        if event.message:
            from_user = event.message.from_user
        if event.callback_query:
            from_user = event.callback_query.from_user
        if event.inline_query:
            from_user = event.inline_query.from_user
        if from_user:
            if from_user.id:
                key = f"{from_user.id}:lang"
                language_code_from_db = r.get(key)
                if language_code_from_db:
                    return language_code_from_db.decode("utf-8")

            language_code_from_user = getattr(from_user, "language_code", None)

            if language_code_from_user:
                return language_code_from_user

            return await super().get_locale(event, data)


i18n_middleware = SimpleI18nMiddleware(i18n)
