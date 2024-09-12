import logging

from aiogram import Bot
from aiogram.types import URLInputFile
from aiohttp.web_request import Request
from aiohttp.web_response import json_response
from redis import Redis

from app.utils.file_utils import get_file_type_by_name
from app.utils.jwt_utils import decode_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def send_file(request: Request):
    bot: Bot = request.app["bot"]
    r: Redis = request.app["r"]
    response_json = {"error": 0}

    try:
        data = await request.json()
        token = request.query.get("token")

        if not token:
            raise ValueError("Token must be provided")

        config = decode_token(token)

        status = data.get("status")
        if status in [2, 3]:
            ds_file_url = data.get("url")
            if not ds_file_url:
                raise ValueError("URL must be provided")

            filename = config["file_name"]
            file_type = get_file_type_by_name(ds_file_url)
            document = URLInputFile(ds_file_url, filename=f"{filename}.{file_type}")

            members = r.hget(config["key"], "members")
            if not members:
                raise ValueError("No members found for the given key")
            members = members.decode("utf-8").split()

            group = r.hget(config["key"], "group")
            if group:
                group = group.decode("utf-8")
                members.append(group)

            for member in members:
                try:
                    # TODO: We cannot translate this string because the user's language is unknown
                    await bot.send_document(
                        chat_id=member,
                        document=document,
                        caption=f"{filename}.{file_type}",
                    )
                except Exception as e:
                    logger.error(f"Failed to send document to user {member}: {e}")

            pipeline = r.pipeline()
            pipeline.hdel(config["key"], "file_unique_id")
            pipeline.hset(config["key"], "members", "")
            pipeline.execute()

    except Exception as e:
        response_json["error"] = 1
        response_json["message"] = str(e)

    return json_response(
        data=response_json, status=500 if response_json["error"] == 1 else 200
    )
