#
# (c) Copyright Ascensio System SIA 2024
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
