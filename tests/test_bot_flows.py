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

"""Smoke: user-facing chat scenarios, driven through the real dispatcher.

Updates are fed to the same routers and middlewares as in production; Bot API
calls are recorded by MockedSession and Redis is FakeRedis. The Document Server
conversion endpoint is a local aiohttp test server.
"""

import asyncio
import datetime
import itertools
import re
import sys

import jwt
import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage, SimpleEventIsolation
from aiogram.methods import EditMessageText, SendDocument, SendMessage
from aiogram.types import CallbackQuery, Chat, Document, Message, Update, User
from fakes import FakeRedis, make_bot

from app.handlers import setup_handlers
from app.keyboards import LangCallback
from app.middlewares import setup_middlewares
from config import BOT_NAME, JWT_HEADER, JWT_SECRET, WEB_APP_NAME

_ids = itertools.count(1)


class Harness:
    """One dispatcher per test session: aiogram routers can only be attached once."""

    def __init__(self):
        self.bot, self.session = make_bot(BOT_NAME)
        self.redis = FakeRedis()
        self.storage = MemoryStorage()
        self.dp = Dispatcher(storage=self.storage, events_isolation=SimpleEventIsolation())
        self.dp["r"] = self.redis
        setup_middlewares(self.dp)
        setup_handlers(self.dp)

    def reset(self):
        self.redis.data.clear()
        self.redis.ttl.clear()
        self.storage.storage.clear()
        self.session.requests.clear()

    def send(self, message: Message):
        update = Update(update_id=next(_ids), message=message)
        asyncio.run(self.dp.feed_update(self.bot, update))
        return message

    def replies(self):
        return [r.text for r in self.session.of(SendMessage)]


@pytest.fixture(scope="module")
def harness_once():
    return Harness()


@pytest.fixture
def h(harness_once):
    harness_once.reset()
    return harness_once


def user(uid, lang="en"):
    return User(id=uid, is_bot=False, first_name=f"User{uid}", language_code=lang)


def private_msg(uid, text=None, document=None, reply_to=None, lang="en"):
    return Message(
        message_id=next(_ids),
        date=datetime.datetime.now(datetime.timezone.utc),
        chat=Chat(id=uid, type="private"),
        from_user=user(uid, lang),
        text=text,
        document=document,
        reply_to_message=reply_to,
    )


def group_msg(uid, text, chat_id=-100500):
    return Message(
        message_id=next(_ids),
        date=datetime.datetime(2026, 1, 2, 15, 4, tzinfo=datetime.timezone.utc),
        chat=Chat(id=chat_id, type="supergroup", title="Team"),
        from_user=user(uid),
        text=text,
    )


def doc(name, size=10_000):
    return Document(file_id=f"FILE-{name}", file_unique_id=f"U-{name}", file_name=name, file_size=size)


def link_key(text):
    m = re.search(rf"https://t\.me/{BOT_NAME}/{WEB_APP_NAME}\?startapp=([0-9a-f]{{32}})", text)
    assert m, f"no Mini App link in: {text!r}"
    return m.group(1)


# --- Menu ---------------------------------------------------------------------------------


def test_start_shows_main_menu(h):
    h.send(private_msg(1, "/start"))
    req = h.session.of(SendMessage)[-1]
    buttons = [b.text for row in req.reply_markup.keyboard for b in row]
    assert buttons == ["Create", "Open", "🔄 Convert", "❌ Cancel"]


def test_cancel_without_action(h):
    h.send(private_msg(2, "/cancel"))
    assert h.replies()[-1] == "There is nothing to cancel"


# --- Create -------------------------------------------------------------------------------


def test_create_document_in_private_chat(h):
    h.send(private_msg(3, "/start"))
    h.send(private_msg(3, "Create"))
    h.send(private_msg(3, "Document"))
    h.send(private_msg(3, "Q3 plan"))

    text = h.replies()[-1]
    key = link_key(text)
    assert "Q3 plan.docx" in text
    session = h.redis.session(key)
    assert session["file_type"] == "docx"
    assert session["document_type"] == "word"
    assert session["owner"] == "3"
    assert "file_id" not in session, "a created file has no Telegram file yet"
    assert h.redis.ttl[key] == 24 * 3600


def test_create_menu_works_in_russian(h):
    for text in ["/start", "Создать", "Электронная таблица", "Бюджет"]:
        h.send(private_msg(4, text, lang="ru"))
    key = link_key(h.replies()[-1])
    assert h.redis.session(key)["file_type"] == "xlsx"


def test_create_rejects_empty_title(h):
    for text in ["/start", "Create", "Document", "..."]:
        h.send(private_msg(5, text))
    assert h.replies()[-1] == "Invalid title"
    assert h.redis.session_keys() == []


def test_create_in_group_by_command(h):
    h.send(group_msg(6, f"/presentation@{BOT_NAME}"))
    text = h.replies()[-1]
    key = link_key(text)
    session = h.redis.session(key)
    assert session["file_type"] == "pptx"
    assert session["group"] == "-100500"
    assert session["file_name"] == "New presentation 2026-01-02_03-04 PM UTC"
    assert "All group members can edit this file." in text


# --- Open ---------------------------------------------------------------------------------


def test_open_editable_file_sent_without_command(h):
    h.send(private_msg(7, document=doc("report.docx")))
    text = h.replies()[-1]
    session = h.redis.session(link_key(text))
    assert session["file_id"] == "FILE-report.docx"
    assert session["file_name"] == "report"
    assert "co-editing" in text


def test_open_view_only_file(h):
    h.send(private_msg(8, document=doc("notes.txt")))
    assert "for viewing" in h.replies()[-1]


def test_open_via_menu(h):
    h.send(private_msg(9, "/start"))
    h.send(private_msg(9, "Open"))
    assert h.replies()[-1] == "Send file"
    h.send(private_msg(9, document=doc("deck.pptx")))
    link_key(h.replies()[-1])


def test_open_unsupported_file(h):
    h.send(private_msg(10, document=doc("archive.zip")))
    assert h.replies()[-1] == "File not supported"
    assert h.redis.session_keys() == []


def test_open_too_large_file(h):
    h.send(private_msg(11, document=doc("big.docx", size=21 * 1024 * 1024)))
    assert "too large" in h.replies()[-1]
    assert h.redis.session_keys() == []


def test_reopen_by_replying_to_file(h):
    original = private_msg(12, document=doc("contract.docx"))
    h.send(private_msg(12, "open again", reply_to=original))
    session = h.redis.session(link_key(h.replies()[-1]))
    assert session["file_id"] == "FILE-contract.docx"


# --- Convert ------------------------------------------------------------------------------


@pytest.fixture
def fake_docserver(monkeypatch):
    calls = []

    async def convert(request):
        calls.append({"json": await request.json(), "headers": dict(request.headers)})
        return web.json_response({"endConvert": True, "fileUrl": "http://docserver.test/out.pdf", "percent": 100})

    app = web.Application()
    app.router.add_post("/ConvertService.ashx", convert)
    loop = asyncio.new_event_loop()
    server = TestServer(app, loop=loop)
    loop.run_until_complete(server.start_server())
    # app.handlers re-exports the router object under the module's name, so patch via sys.modules.
    monkeypatch.setattr(
        sys.modules["app.handlers.convert_router"], "DOCSERVER_URL", str(server.make_url("")).rstrip("/")
    )
    yield calls, loop
    loop.run_until_complete(server.close())
    loop.close()


def test_convert_file(h, fake_docserver):
    calls, loop = fake_docserver

    def send(message):
        loop.run_until_complete(h.dp.feed_update(h.bot, Update(update_id=next(_ids), message=message)))

    send(private_msg(13, "/start"))
    send(private_msg(13, "🔄 Convert"))
    send(private_msg(13, document=doc("report.docx")))
    keyboard = h.session.of(SendMessage)[-1].reply_markup.keyboard
    assert "PDF" in [b.text for row in keyboard for b in row]

    send(private_msg(13, "PDF"))

    assert len(calls) == 1
    body = calls[0]["json"]
    assert body["filetype"] == "docx" and body["outputtype"] == "pdf"
    assert "/editor/getFile?security_token=" in body["url"]
    jwt.decode(calls[0]["headers"][JWT_HEADER].removeprefix("Bearer "), JWT_SECRET, algorithms=["HS256"])

    sent = h.session.of(SendDocument)
    assert len(sent) == 1
    assert sent[0].document.filename == "report.pdf"


def test_convert_rejects_format_not_in_list(h):
    for message in [
        private_msg(14, "/start"),
        private_msg(14, "🔄 Convert"),
        private_msg(14, document=doc("report.docx")),
        private_msg(14, "MP3"),
    ]:
        h.send(message)
    assert h.replies()[-1] == "Invalid format"


# --- Language -----------------------------------------------------------------------------


def test_change_language(h):
    h.send(private_msg(15, "/lang"))
    keyboard = h.session.of(SendMessage)[-1].reply_markup.inline_keyboard
    assert "Русский" in [b.text for row in keyboard for b in row]

    callback = CallbackQuery(
        id="cb",
        from_user=user(15),
        chat_instance="ci",
        data=LangCallback(lang="ru", user_id=15).pack(),
        message=private_msg(15, "Available languages:"),
    )
    asyncio.run(h.dp.feed_update(h.bot, Update(update_id=next(_ids), callback_query=callback)))
    assert h.redis.get("15:lang") == b"ru"
    assert h.session.of(EditMessageText)[-1].text == "Язык изменен"

    h.send(private_msg(15, "/start"))
    buttons = [b.text for row in h.session.of(SendMessage)[-1].reply_markup.keyboard for b in row]
    assert buttons[0] == "Создать"


# --- Anti-flood ---------------------------------------------------------------------------


def test_flood_is_throttled(h):
    for _ in range(6):
        h.send(private_msg(16, "hello"))
    assert any("Too many requests" in t for t in h.replies())
