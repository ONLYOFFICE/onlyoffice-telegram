#
# (c) Copyright Ascensio System SIA 2024
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

from aiohttp.web_app import Application

from .editor import editor
from .get_config import get_config
from .get_file import get_file
from .get_locales import get_locales
from .send_file import send_file


def setup_routers(app: Application) -> None:
    app.router.add_static(prefix="/static", path="static")
    app.router.add_get("/editor", editor)
    app.router.add_get("/editor/getConfig", get_config)
    app.router.add_get("/editor/getFile", get_file)
    app.router.add_get("/editor/getLocales", get_locales)
    app.router.add_post("/editor/sendFile", send_file)
