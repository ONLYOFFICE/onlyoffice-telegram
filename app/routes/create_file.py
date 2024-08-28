import logging

from aiohttp.web_request import Request
from aiohttp.web_response import Response, json_response

from app.utils.file_utils import get_file_by_file_type

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_file(request: Request) -> Response:
    file_type = request.query.get("file_type")

    if not file_type:
        return json_response(
            {"ok": False, "error": "file_type is required"}, status=400
        )

    try:
        file_data = get_file_by_file_type(file_type)
        response = Response(body=file_data, content_type="application/octet-stream")
        response.headers["Content-Disposition"] = "attachment;"
        return response

    except Exception as e:
        logger.error(f"Failed to create document to documentserver: {e}")
        return json_response({"ok": False, "error": str(e)}, status=500)
