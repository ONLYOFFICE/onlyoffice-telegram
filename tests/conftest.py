#
# (c) Copyright Ascensio System SIA 2026
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

"""Smoke-test setup.

config.py reads the environment at import time, so the test environment must be
in place before anything from `app` or `config` is imported. No real Telegram,
Document Server or Redis is used: see tests/fakes.py.
"""

import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

TEST_ENV = {
    "BOT_NAME": "TestOnlyofficeBot",
    "BOT_TOKEN": "42:TEST-TOKEN-NOT-REAL",
    "DOCSERVER_URL": "http://docserver.test",
    "JWT_SECRET": "test-jwt-secret",
    "JWT_HEADER": "AuthorizationJWT",
    "REDIS_DB": "0",
    "REDIS_HOST": "localhost",
    "REDIS_PORT": "6379",
    "TTL": "24",
    "WEB_APP_NAME": "editor",
    "WEB_APP_URL": "http://bot.test",
    "WEBHOOK_HOST": "127.0.0.1",
    "WEBHOOK_PATH": "/webhook",
    "WEBHOOK_PORT": "8000",
}
os.environ.update(TEST_ENV)

# app.routes registers static files with a path relative to the working directory.
os.chdir(ROOT)

FORMATS_JSON = ROOT / "static" / "assets" / "document-formats" / "onlyoffice-docs-formats.json"
TEMPLATES_DIR = ROOT / "static" / "assets" / "document-templates" / "default"

if not FORMATS_JSON.exists() or not TEMPLATES_DIR.exists():
    pytest.exit("Submodules are missing. Run: git submodule update --init", returncode=2)
