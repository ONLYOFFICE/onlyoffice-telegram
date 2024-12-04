import logging

from aiogram import Bot
from aiogram.types import URLInputFile
from aiohttp.web_request import Request
from aiohttp.web_response import json_response
from redis import Redis

from app.utils.file_utils import get_extension_by_name
from app.utils.jwt_utils import decode_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def send_file(request: Request):
    bot: Bot = request.app["bot"]
    r: Redis = request.app["r"]
    security_token = request.query.get("security_token")
    key = decode_token(security_token).get("key", None)
    response_json = {"error": 0}

    if not key:
        raise ValueError("key must be provided")

    try:
        data = await request.json()
        status = data.get("status")
        if status in [2, 3]:
            ds_file_url = data.get("url")
            if not ds_file_url:
                raise ValueError("URL must be provided")

            filename = r.hget(key, "file_name").decode("utf-8")
            file_type = get_extension_by_name(ds_file_url)
            document = URLInputFile(ds_file_url, filename=f"{filename}.{file_type}")

            owner = r.hget(key, "owner").decode("utf-8")
            message_id = r.hget(key, "message_id").decode("utf-8")
            members = r.hget(key, "members")
            if not members:
                raise ValueError("No members found for the given key")
            members = members.decode("utf-8").split()

            group = r.hget(key, "group")
            if group:
                group = group.decode("utf-8")
                members.append(group)

            for member in members:
                try:
                    # TODO: We cannot translate this string because the user's language is unknown
                    if member == owner:
                        try:
                            await bot.set_message_reaction(member, message_id, None)
                            await bot.send_document(
                                chat_id=member,
                                document=document,
                                caption=f"{filename}.{file_type}",
                                reply_to_message_id=message_id,
                            )
                        except Exception:
                            await bot.send_document(
                                chat_id=member,
                                document=document,
                                caption=f"{filename}.{file_type}",
                            )
                    else:
                        await bot.send_document(
                            chat_id=member,
                            document=document,
                            caption=f"{filename}.{file_type}",
                        )
                except Exception as e:
                    logger.error(f"Failed to send document to user {member}: {e}")

            pipeline = r.pipeline()
            pipeline.hdel(key, "key")
            pipeline.hset(key, "members", "")
            pipeline.execute()

    except Exception as e:
        response_json["error"] = 1
        response_json["message"] = str(e)

    return json_response(
        data=response_json, status=500 if response_json["error"] == 1 else 200
    )
