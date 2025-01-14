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

import logging

from aiogram import Bot
from aiogram.types import URLInputFile
from aiohttp.web_request import Request
from aiohttp.web_response import json_response
from redis import Redis

from app.utils.file_utils import get_extension_by_name
from app.utils.jwt_utils import decode_token
from app.utils.lang_utils import _
from config import JWT_HEADER

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def send_file(request: Request):
    try:
        authorization = request.headers.get(JWT_HEADER)
        header_jwt = authorization[len("Bearer ") :]
        decode_token(header_jwt)
    except Exception as e:
        logger.error(f"Error when checking jwt: {e}")
        return json_response({"ok": False, "error": str(e)}, status=403)

    bot: Bot = request.app["bot"]
    r: Redis = request.app["r"]

    response_json = {"error": 0}

    try:
        data = await request.json()
        status = data.get("status")
        if status in [2, 3]:
            security_token = request.query.get("security_token")
            key = decode_token(security_token).get("key", None)
            if not key:
                raise ValueError("key must be provided")

            ds_file_url = data.get("url")
            if not ds_file_url:
                raise ValueError("URL must be provided")

            pipeline = r.pipeline()
            pipeline.hgetall(key)
            results = pipeline.execute()
            config = {}
            for field, value in results[0].items():
                config[field.decode("utf-8")] = value.decode("utf-8")

            file_type = get_extension_by_name(ds_file_url)
            document = URLInputFile(ds_file_url, filename=f"{config['file_name']}.{file_type}")

            if not config["members"]:
                raise ValueError("No members found for the given key")
            config["members"] = config["members"].split()

            if "group" in config:
                config["members"].append(config["group"])

            for member in config["members"]:
                try:
                    lang = r.get(f"{member}:lang")
                    if not lang:
                        lang = config.get("lang", "en")
                    else:
                        lang = lang.decode("utf-8")
                    if lang == "default":
                        lang = "en"
                    caption = _("Your file is ready. Please find the final version here.", locale=lang)
                    if member == config["owner"]:
                        try:
                            await bot.set_message_reaction(member, config["link_message_id"], None)
                            link_messages = {
                                "01": _("Your file", locale=lang),
                                "02": _("To start co-editing, send this message to other participants.", locale=lang),
                                "03": _("The ONLYOFFICE editor link:", locale=lang),
                                "04": _("expired", locale=lang),
                            }
                            edited_text = f"{link_messages['01']} <b>{config['file_name']}.{config['file_type']}</b>\n{link_messages['02']}\n\n{link_messages['03']} {link_messages['04']}"
                            await bot.edit_message_text(
                                text=edited_text, chat_id=member, message_id=config["link_message_id"]
                            )
                        except Exception as e:
                            logger.error(f"Error edit_message_text on message with link to editor: {e}")

                        try:
                            await bot.set_message_reaction(member, config["message_id"], None)
                            await bot.send_document(
                                chat_id=member,
                                document=document,
                                caption=caption,
                                reply_to_message_id=config["message_id"],
                            )
                        except Exception as e:
                            logger.error(f"Error send document with reply_to_message_id param: {e}")
                            await bot.send_document(chat_id=member, document=document, caption=caption)
                    else:
                        await bot.send_document(chat_id=member, document=document, caption=caption)
                except Exception as e:
                    logger.error(f"Failed to send document to user {member}: {e}")

            r.delete(key)

    except Exception as e:
        logger.error(f"Failed to send document: {e}")
        response_json["error"] = 1
        response_json["message"] = str(e)

    return json_response(data=response_json, status=500 if response_json["error"] == 1 else 200)
