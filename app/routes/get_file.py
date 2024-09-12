import logging

from aiogram import Bot
from aiohttp.web_request import Request
from aiohttp.web_response import Response, json_response

from app.utils.file_utils import get_file_by_file_type
from app.utils.jwt_utils import decode_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_file(request: Request) -> Response:
    bot: Bot = request.app["bot"]
    token = request.query.get("token")

    if not token:
        return json_response({"ok": False, "error": "token is required"}, status=400)

    try:
        config = decode_token(token)

        if "file_id" in config:
            file = await bot.get_file(config["file_id"])
            file_path = file.file_path
            file_data = await bot.download_file(file_path)
        else:
            file_data = get_file_by_file_type(config["file_type"])

        response = Response(body=file_data, content_type="application/octet-stream")
        response.headers["Content-Disposition"] = "attachment;"
        return response

    except Exception as e:
        logger.error(f"Failed to send document to documentserver: {e}")
        return json_response({"ok": False, "error": str(e)}, status=500)
