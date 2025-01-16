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

from aiohttp.web import Request, Response
from jinja2 import Environment, FileSystemLoader

from config import DESKTOP_MODE, DOCSERVER_URL, PROJECT_ROOT

env = Environment(loader=FileSystemLoader(PROJECT_ROOT / "static"))
template = env.get_template("editor.html")


async def editor(request: Request) -> Response:  # pylint: disable=unused-argument
    html_content = template.render(DOCSERVER_URL=DOCSERVER_URL, DESKTOP_MODE=json.dumps(DESKTOP_MODE))
    return Response(text=html_content, content_type="text/html")
