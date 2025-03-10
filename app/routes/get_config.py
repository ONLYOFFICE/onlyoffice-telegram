#
# (c) Copyright Ascensio System SIA 2025
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

import json
import logging
import urllib.parse
import uuid

from aiogram import Bot
from aiogram.utils.web_app import check_webapp_signature
from aiohttp.web_request import Request
from aiohttp.web_response import json_response
from redis import Redis

from app.utils.file_utils import get_format_by_extension
from app.utils.jwt_utils import create_token, encode_payload
from config import TTL, WEB_APP_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_config(request: Request):
    try:
        bot: Bot = request.app["bot"]
        r: Redis = request.app["r"]

        data = request.query
        auth = data.get("_auth")

        if not auth or not check_webapp_signature(bot.token, auth):
            return json_response({"ok": False, "error": "Unauthorized"}, status=401)

        decoded_auth = urllib.parse.unquote(auth)
        auth_params = urllib.parse.parse_qs(decoded_auth)

        if "user" not in auth_params or "start_param" not in auth_params:
            return json_response({"ok": False, "error": "Bad Request"}, status=400)

        user = json.loads(auth_params["user"][0])
        key = auth_params["start_param"][0]

        pipeline = r.pipeline()
        pipeline.hgetall(key)
        pipeline.get(f"{user['id']}:lang")
        results = pipeline.execute()

        if not results[0]:
            return json_response({"ok": False, "error": "The link has expired"}, status=410)

        session = {}
        for field, value in results[0].items():
            session[field.decode("utf-8")] = value.decode("utf-8")

        pipeline = r.pipeline()

        if "key" not in session:
            session["key"] = uuid.uuid4().hex
            pipeline.hset(key, "key", session["key"])

        user_id = str(user["id"])
        members = set(session["members"].split())
        if user_id not in members:
            members.add(user_id)
            session["members"] = " ".join(members)
            pipeline.hset(key, "members", session["members"])

        pipeline.expire(f"{key}", TTL)
        pipeline.execute()

        session["lang"] = results[1].decode("utf-8") if results[1] else user.get("language_code", "en")

        f = get_format_by_extension(session["file_type"])

        mode = "edit" if "edit" in f["actions"] else "view"
        security_token = create_token(key)
        config = {
            "document": {
                "fileType": session["file_type"],
                "key": session["key"],
                "permissions": {
                    "download": False,
                    "print": False,
                    "protect": False,
                },
                "title": f"{session['file_name']}.{session['file_type']}",
                "url": f"{WEB_APP_URL}/editor/getFile?security_token={security_token}",
            },
            "documentType": session["document_type"],
            "editorConfig": {
                "customization": {
                    "compactHeader": True,
                    "toolbarNoTabs": True,
                    "logo": {"visible": False},
                },
                "lang": session["lang"],
                "mode": mode,
                "user": {
                    "id": str(user.get("id", "")),
                    "name": user.get("first_name", ""),
                },
            },
        }
        if mode == "edit":
            callback_url = f"{WEB_APP_URL}/editor/sendFile?security_token={security_token}"
            config["editorConfig"]["callbackUrl"] = callback_url
        if "file_id" not in session:  # This is file creation
            config["editorConfig"]["customization"]["mobile"] = {
                "forceView": False,
                "standardView": False,
            }
        token = encode_payload(config)
        config["token"] = token

        return json_response({"ok": True, "config": config})
    except Exception as e:
        logger.error(f"Failed to get config: {e}")
        return json_response({"ok": False, "error": str(e)}, status=500)
