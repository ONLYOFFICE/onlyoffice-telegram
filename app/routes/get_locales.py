from aiohttp.web_request import Request
from aiohttp.web_response import json_response

from app.utils.lang_utils import _


async def get_locales(request: Request):
    lang = {
        "title": _("Not available"),
        "description": _(
            "The link has expired. Please create a new one or open this file in the chat."
        ),
    }
    return json_response(lang)
