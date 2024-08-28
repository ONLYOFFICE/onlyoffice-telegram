import logging

from aiogram import Bot
from aiohttp.web_request import Request
from aiohttp.web_response import Response, json_response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_file(request: Request) -> Response:
    bot: Bot = request.app["bot"]
    file_id = request.query.get("file_id")

    if not file_id:
        return json_response({"ok": False, "error": "file_id is required"}, status=400)

    try:
        file = await bot.get_file(file_id)
        file_path = file.file_path
        file_data = await bot.download_file(file_path)
        response = Response(body=file_data, content_type="application/octet-stream")
        response.headers["Content-Disposition"] = "attachment;"
        return response

    except Exception as e:
        logger.error(f"Failed to send document to documentserver: {e}")
        return json_response({"ok": False, "error": str(e)}, status=500)
