import json
import logging
import urllib.parse
import uuid

from aiogram import Bot
from aiogram.utils.web_app import check_webapp_signature
from aiohttp.web_request import Request
from aiohttp.web_response import json_response
from redis import Redis

from app.utils.jwt_utils import decode_token, encode_payload
from config import TTL, WEB_APP_URL

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
        key = auth_params["start_param"][0]

        pipeline = r.pipeline()
        pipeline.hgetall(key)
        pipeline.get(f"{user['id']}:lang")
        results = pipeline.execute()

        session = {}
        for field, value in results[0].items():
            session[field.decode("utf-8")] = value.decode("utf-8")

        pipeline = r.pipeline()

        if "token" not in session:
            config = {
                "document": {
                    "key": uuid.uuid4().hex,
                    "permissions": {"download": "false", "print": "false"},
                    "url": f"${WEB_APP_URL}/editor/getFile?key={key}",
                },
                "editorConfig": {
                    "callbackUrl": f"${WEB_APP_URL}/editor/sendFile?key={key}",
                },
            }
            token = encode_payload(config)
            session["token"] = token
            pipeline.hset(key, "token", token)
        else:
            config = decode_token(session["token"])

        user_id = str(user["id"])
        members = set(session["members"].split())
        if user_id not in members:
            members.add(user_id)
            session["members"] = " ".join(members)
            pipeline.hset(key, "members", session["members"])

        pipeline.expire(f"{key}", TTL)
        pipeline.execute()

        lang = (
            results[1].decode("utf-8")
            if results[1]
            else user.get("language_code", "en")
        )
        session["lang"] = lang

        return json_response(
            {
                "ok": True,
                "config": {
                    "document": {
                        "fileType": session["file_type"],
                        "key": config["document"]["key"],
                        "permissions": {"download": "false", "print": "false"},
                        "title": f"{session['file_name']}.{session['file_type']}",
                        "url": config["document"]["url"],
                    },
                    "documentType": session["document_type"],
                    "editorConfig": {
                        "callbackUrl": config["editorConfig"]["callbackUrl"],
                        "lang": session["lang"],
                    },
                    "token": session["token"],
                },
            }
        )
    except Exception as e:
        logger.error(f"Failed to get config: {e}")
        return json_response({"ok": False, "error": str(e)}, status=500)
