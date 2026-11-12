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

"""Smoke: the HTTP side — Mini App page, editor config, Document Server file/callback endpoints."""

import asyncio

import jwt
import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
from aiogram.methods import EditMessageText, SendDocument
from fakes import FakeRedis, make_bot, make_init_data

from app.routes import setup_routers
from app.utils.jwt_utils import create_token, encode_payload
from config import BOT_NAME, BOT_TOKEN, DOCSERVER_URL, JWT_HEADER, JWT_SECRET, WEB_APP_URL

KEY = "a" * 32
OWNER = {"id": 1001, "first_name": "Owner", "language_code": "en"}
GUEST = {"id": 2002, "first_name": "Guest", "language_code": "de"}


def new_session(redis, **overrides):
    session = {
        "document_type": "word",
        "file_name": "Plan",
        "file_type": "docx",
        "lang": "en",
        "members": "",
        "message_id": 1,
        "owner": OWNER["id"],
        "link_message_id": 2,
    }
    session.update(overrides)
    redis.hset(KEY, mapping=session)
    return session


def run(scenario):
    """Run `scenario(client, redis, session)` against a fresh app."""
    bot, tg = make_bot(BOT_NAME)
    redis = FakeRedis()
    app = web.Application()
    app["bot"] = bot
    app["r"] = redis
    setup_routers(app)

    async def main():
        async with TestClient(TestServer(app)) as client:
            return await scenario(client, redis, tg)

    return asyncio.run(main())


def ds_headers(payload=None):
    return {JWT_HEADER: "Bearer " + encode_payload(payload or {"any": "payload"})}


async def get_config(client, user, key=KEY):
    init_data = make_init_data(BOT_TOKEN, user, key)
    return await client.get("/editor/getConfig", params={"_auth": init_data})


# --- Mini App page ------------------------------------------------------------------------


def test_editor_page_loads_docs_api():
    async def scenario(client, redis, tg):
        resp = await client.get("/editor")
        assert resp.status == 200
        assert f"{DOCSERVER_URL}/web-apps/apps/api/documents/api.js" in await resp.text()

    run(scenario)


def test_static_logo_is_served():
    async def scenario(client, redis, tg):
        assert (await client.get("/static/logo.svg")).status == 200

    run(scenario)


# --- getConfig ----------------------------------------------------------------------------


def test_config_requires_valid_telegram_signature():
    async def scenario(client, redis, tg):
        new_session(redis)
        assert (await client.get("/editor/getConfig")).status == 401
        forged = make_init_data("1:OTHER-TOKEN", OWNER, KEY)
        assert (await client.get("/editor/getConfig", params={"_auth": forged})).status == 401

    run(scenario)


def test_config_for_expired_link():
    async def scenario(client, redis, tg):
        resp = await get_config(client, OWNER)
        assert resp.status == 410

    run(scenario)


def test_config_for_new_file_is_signed_and_editable():
    async def scenario(client, redis, tg):
        new_session(redis)
        resp = await get_config(client, OWNER)
        assert resp.status == 200
        config = (await resp.json())["config"]

        assert config["editorConfig"]["mode"] == "edit"
        assert config["editorConfig"]["callbackUrl"].startswith(f"{WEB_APP_URL}/editor/sendFile?security_token=")
        assert config["document"]["url"].startswith(f"{WEB_APP_URL}/editor/getFile?security_token=")
        assert config["document"]["title"] == "Plan.docx"
        assert config["editorConfig"]["customization"]["mobile"] == {"forceView": False, "standardView": False}
        signed = jwt.decode(config.pop("token"), JWT_SECRET, algorithms=["HS256"])
        assert signed["document"]["key"] == config["document"]["key"]

        assert redis.session(KEY)["members"] == str(OWNER["id"])
        assert redis.ttl[KEY] == 24 * 3600

    run(scenario)


def test_co_editors_share_one_document_key():
    async def scenario(client, redis, tg):
        new_session(redis, file_id="TG-FILE")
        first = (await (await get_config(client, OWNER)).json())["config"]
        second = (await (await get_config(client, GUEST)).json())["config"]

        assert first["document"]["key"] == second["document"]["key"]
        assert second["editorConfig"]["user"] == {"id": str(GUEST["id"]), "name": "Guest"}
        assert second["editorConfig"]["lang"] == "de"
        assert set(redis.session(KEY)["members"].split()) == {str(OWNER["id"]), str(GUEST["id"])}

    run(scenario)


def test_config_for_view_only_format():
    async def scenario(client, redis, tg):
        new_session(redis, file_type="txt", file_id="TG-FILE")
        config = (await (await get_config(client, OWNER)).json())["config"]
        assert config["editorConfig"]["mode"] == "view"
        assert "callbackUrl" not in config["editorConfig"]

    run(scenario)


# --- getFile (Document Server downloads the source) --------------------------------------


@pytest.mark.parametrize("headers", [{}, {JWT_HEADER: "Bearer not-a-jwt"}])
def test_get_file_requires_docserver_jwt(headers):
    async def scenario(client, redis, tg):
        new_session(redis)
        resp = await client.get("/editor/getFile", params={"security_token": create_token(KEY)}, headers=headers)
        assert resp.status == 403

    run(scenario)


def test_get_file_serves_blank_template_for_created_file():
    async def scenario(client, redis, tg):
        new_session(redis)
        resp = await client.get("/editor/getFile", params={"security_token": create_token(KEY)}, headers=ds_headers())
        assert resp.status == 200
        assert (await resp.read()).startswith(b"PK")

    run(scenario)


def test_get_file_proxies_telegram_file_for_opened_file():
    async def scenario(client, redis, tg):
        new_session(redis, file_id="TG-FILE")
        resp = await client.get("/editor/getFile", params={"security_token": create_token(KEY)}, headers=ds_headers())
        assert resp.status == 200
        assert await resp.read() == tg.download_content

    run(scenario)


# --- sendFile (Document Server callback) --------------------------------------------------


def callback(client, body, headers=None):
    return client.post(
        "/editor/sendFile",
        params={"security_token": create_token(KEY)},
        json=body,
        headers=ds_headers(body) if headers is None else headers,
    )


def test_callback_requires_docserver_jwt():
    async def scenario(client, redis, tg):
        new_session(redis)
        resp = await callback(client, {"status": 2, "url": "http://docserver.test/x.docx"}, headers={})
        assert resp.status == 403

    run(scenario)


def test_callback_while_editing_is_acknowledged_without_sending():
    async def scenario(client, redis, tg):
        new_session(redis, members=str(OWNER["id"]))
        resp = await callback(client, {"status": 1})
        assert resp.status == 200 and (await resp.json())["error"] == 0
        assert tg.of(SendDocument) == []
        assert redis.session(KEY), "session must survive while editing"

    run(scenario)


def test_callback_on_close_sends_file_to_every_member_and_ends_session():
    async def scenario(client, redis, tg):
        new_session(redis, members=f"{OWNER['id']} {GUEST['id']}")
        resp = await callback(client, {"status": 2, "url": "http://docserver.test/cache/output.docx"})
        assert resp.status == 200 and (await resp.json())["error"] == 0

        recipients = sorted(str(m.chat_id) for m in tg.of(SendDocument))
        assert recipients == sorted([str(OWNER["id"]), str(GUEST["id"])])
        assert all(m.document.filename == "Plan.docx" for m in tg.of(SendDocument))
        edited = tg.of(EditMessageText)
        assert len(edited) == 1 and "expired" in edited[0].text, "owner's link message is marked expired"
        assert redis.session(KEY) == {}, "link must stop working after the file is returned"

    run(scenario)


# --- getLocales (expired-link page texts) -------------------------------------------------


def test_expired_link_page_is_localized():
    async def scenario(client, redis, tg):
        resp = await client.get("/editor/getLocales", params={"_auth": "", "lang": "ru"})
        assert (await resp.json())["title"] == "Срок действия ссылки истек"

    run(scenario)
