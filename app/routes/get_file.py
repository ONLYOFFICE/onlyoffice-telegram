import logging

from aiogram import Bot
from aiohttp.web_request import Request
from aiohttp.web_response import Response, json_response
from redis import Redis

from app.utils.file_utils import get_file_by_file_type

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_file(request: Request) -> Response:
    bot: Bot = request.app["bot"]
    r: Redis = request.app["r"]
    key = request.query.get("key")

    if not key:
        return json_response({"ok": False, "error": "key is required"}, status=400)

    try:
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
