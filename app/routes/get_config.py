import json
import logging
import urllib.parse

from aiogram import Bot
from aiogram.utils.web_app import check_webapp_signature
from aiohttp.web_request import Request
from aiohttp.web_response import json_response
from redis import Redis

from config import TTL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_config(request: Request):
    try:
        bot: Bot = request.app["bot"]
        r: Redis = request.app["r"]

        data = request.query
        auth = data.get("_auth")

        if not auth or not check_webapp_signature(bot.token, auth):
            return json_response({"ok": False, "error": "Unauthorized"}, status=401)

        decoded_auth = urllib.parse.unquote(auth)
        auth_params = urllib.parse.parse_qs(decoded_auth)

        if "user" not in auth_params or "start_param" not in auth_params:
            return json_response({"ok": False, "error": "Bad Request"}, status=400)

        user = json.loads(auth_params["user"][0])
        key = auth_params["start_param"][0].replace("_", ":", 1)

        pipeline = r.pipeline()
        pipeline.hgetall(f"{key}:config")
        pipeline.sadd(f"{key}:members", user["id"])
        pipeline.expire(f"{key}:members", TTL)
        results = pipeline.execute()

        config = {}
        for key, value in results[0].items():
            config[key.decode("utf-8")] = value.decode("utf-8")

        return json_response({"ok": True, "config": config})
    except Exception as e:
        logger.error(f"Failed to get config: {e}")
        return json_response({"ok": False, "error": str(e)}, status=500)
