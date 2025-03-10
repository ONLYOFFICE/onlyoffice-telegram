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

from aiohttp.web_request import Request
from aiohttp.web_response import json_response
from redis import Redis

from app.utils.lang_utils import _

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_locales(request: Request):
    lang = None
    try:
        r: Redis = request.app["r"]

        data = request.query
        auth = data.get("_auth")
        decoded_auth = urllib.parse.unquote(auth)
        auth_params = urllib.parse.parse_qs(decoded_auth)

        if "user" in auth_params:
            user = json.loads(auth_params["user"][0])
            lang = r.get(f"{user['id']}:lang").decode("utf-8")
    except Exception as e:
        logger.error(f"Failed to get lang for locales: {e}")

    if not lang:
        lang = data.get("lang", "en")

    locales = {
        "title": _("The link has expired", locale=lang),
        "description": _(
            "Please create a new one by opening this file again in the chat.",
            locale=lang,
        ),
    }
    return json_response(locales)
