import logging

from aiogram import Bot
from aiogram.types import URLInputFile
from aiohttp.web_request import Request
from aiohttp.web_response import json_response
from redis import Redis

from app.utils.file_utils import get_file_type
from config import TTL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def send_file(request: Request):
    bot: Bot = request.app["bot"]
    r: Redis = request.app["r"]
    response_json = {"error": 0}

    try:
        data = await request.json()
        key = request.query.get("key")

        if not key:
            raise ValueError("Key must be provided")

        key = key.replace("_", ":", 1)

        status = data.get("status")
        if status in [2, 3]:
            ds_file_url = data.get("url")
            if not ds_file_url:
                raise ValueError("URL must be provided")

            filename = r.hget(f"{key}:config", "file_name").decode("utf-8")
            file_type = get_file_type(ds_file_url)
            document = URLInputFile(ds_file_url, filename=f"{filename}.{file_type}")

            members = r.smembers(f"{key}:members")
            if not members:
                raise ValueError("No members found for the given key")

            members = [
                res.decode("utf-8") if isinstance(res, bytes) else res
                for res in members
            ]
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
            pipeline.delete(f"{key}:members")
            pipeline.expire(f"{key}:config", TTL)
            pipeline.execute()

    except Exception as e:
        response_json["error"] = 1
        response_json["message"] = str(e)

    return json_response(
        data=response_json, status=500 if response_json["error"] == 1 else 200
    )
