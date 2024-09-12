import os
from pathlib import Path

BOT_NAME = "ONLYOFFICE_test_bot"
BOT_TOKEN = os.getenv("BOT_TOKEN")

CONVERT_MAX_ATTEMPTS = 5
CONVERT_TIMEOUT = 5

DOCSERVER_URL = os.getenv("DOCSERVER_URL")
DOCSERVER_CONVERTER_URL = "ConvertService.ashx"

FLOOD_INTERVAL = 2
FLOOD_MESSAGES_LIMIT = 5
FLOOD_TTL = 3600

MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # TODO: Create Middleware for file size limit

PROJECT_ROOT = Path(__file__).resolve().parent

I18N_PATH = f"{PROJECT_ROOT}/locales"
I18N_DOMAIN = "messages"

REDIS_DB = int(os.getenv("REDIS_DB"))
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))

TTL = 3600 * 24

WEB_APP_NAME = "ONLYOFFICE"
WEB_APP_URL = os.getenv("WEB_APP_URL")

WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT"))
