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

import os
from pathlib import Path

BOT_NAME = os.getenv("BOT_NAME")
BOT_TOKEN = os.getenv("BOT_TOKEN")

CONVERT_MAX_ATTEMPTS = 5
CONVERT_TIMEOUT = 5

DESKTOP_MODE = True

DOCSERVER_URL = os.getenv("DOCSERVER_URL")
DOCSERVER_CONVERTER_URL = "ConvertService.ashx"

FLOOD_INTERVAL = 2
FLOOD_MESSAGES_LIMIT = 5
FLOOD_TTL = 3600

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_HEADER = os.getenv("JWT_HEADER")

MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # TODO: Create Middleware for file size limit

PROJECT_ROOT = Path(__file__).resolve().parent

I18N_PATH = f"{PROJECT_ROOT}/locales"
I18N_DOMAIN = "messages"

REDIS_DB = int(os.getenv("REDIS_DB"))
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))

TTL = 3600 * 24

WEB_APP_NAME = os.getenv("WEB_APP_NAME")
WEB_APP_URL = os.getenv("WEB_APP_URL")

WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT"))
