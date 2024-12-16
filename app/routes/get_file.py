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

import logging

from aiogram import Bot
from aiohttp.web_request import Request
from aiohttp.web_response import Response, json_response
from redis import Redis

from app.utils.file_utils import get_file_by_file_type
from app.utils.jwt_utils import decode_token
from config import JWT_HEADER

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_file(request: Request) -> Response:
    try:
        authorization = request.headers.get(JWT_HEADER)
        header_jwt = authorization[len("Bearer ") :]
        decode_token(header_jwt)
    except Exception as e:
        logger.error(f"Error when checking jwt: {e}")
        return json_response({"ok": False, "error": str(e)}, status=403)

    bot: Bot = request.app["bot"]
    r: Redis = request.app["r"]

    try:
        security_token = request.query.get("security_token")
        key = decode_token(security_token).get("key", None)
        if not key:
            raise ValueError("key must be provided")

        file_id = r.hget(key, "file_id")

        if file_id:
            file = await bot.get_file(file_id.decode("utf-8"))
            file_path = file.file_path
            file_data = await bot.download_file(file_path)
        else:
            lang = r.hget(key, "lang")
            lang = lang.decode("utf-8") if lang else "default"
            file_type = r.hget(key, "file_type")
            file_data = get_file_by_file_type(file_type.decode("utf-8"), lang)

        response = Response(body=file_data, content_type="application/octet-stream")
        response.headers["Content-Disposition"] = "attachment;"
        return response

    except Exception as e:
        logger.error(f"Failed to send document to documentserver: {e}")
        return json_response({"ok": False, "error": str(e)}, status=500)
