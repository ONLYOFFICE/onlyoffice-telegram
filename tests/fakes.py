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

"""In-memory stand-ins for Redis and the Telegram Bot API."""

import datetime
import hashlib
import hmac
import itertools
import json
import time
from urllib.parse import urlencode

from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.methods import EditMessageText, GetFile, GetMe, SendDocument, SendMessage
from aiogram.types import Chat, File, Message, User


def _to_bytes(value):
    if isinstance(value, bytes):
        return value
    return str(value).encode("utf-8")


class FakeRedis:
    """The subset of the synchronous redis-py client the bot uses."""

    def __init__(self):
        self.data = {}
        self.ttl = {}

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        self.data[key] = _to_bytes(value)

    def hget(self, key, field):
        return self.data.get(key, {}).get(_to_bytes(field))

    def hset(self, key, field=None, value=None, mapping=None):
        h = self.data.setdefault(key, {})
        if field is not None:
            h[_to_bytes(field)] = _to_bytes(value)
        for k, v in (mapping or {}).items():
            h[_to_bytes(k)] = _to_bytes(v)

    def hgetall(self, key):
        return dict(self.data.get(key, {}))

    def expire(self, key, seconds):
        self.ttl[key] = seconds

    def delete(self, key):
        self.data.pop(key, None)
        self.ttl.pop(key, None)

    def pipeline(self):
        return FakePipeline(self)

    def session(self, key):
        """Decoded session hash, or {} if absent."""
        return {k.decode(): v.decode() for k, v in self.hgetall(key).items()}

    def session_keys(self):
        return [k for k, v in self.data.items() if isinstance(v, dict) and b"owner" in v]


class FakePipeline:
    def __init__(self, redis):
        self.redis = redis
        self.calls = []

    def __getattr__(self, name):
        def queue(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            return self

        return queue

    def execute(self):
        results = [getattr(self.redis, name)(*args, **kwargs) for name, args, kwargs in self.calls]
        self.calls = []
        return results


class MockedSession(BaseSession):
    """Records every Bot API call instead of sending it."""

    def __init__(self, bot_username):
        super().__init__()
        self.requests = []
        self.bot_username = bot_username
        self.download_content = b"TELEGRAM-FILE-CONTENT"
        self._ids = itertools.count(1000)

    async def close(self):
        pass

    async def make_request(self, bot, method, timeout=None):
        self.requests.append(method)
        if isinstance(method, GetMe):
            return User(id=42, is_bot=True, first_name="Bot", username=self.bot_username)
        if isinstance(method, (SendMessage, SendDocument)):
            # Bind to the bot like a real response, so message.delete()/answer() work.
            return Message(
                message_id=next(self._ids),
                date=datetime.datetime.now(),
                chat=Chat(id=int(method.chat_id), type="private"),
                text=getattr(method, "text", None),
            ).as_(bot)
        if isinstance(method, GetFile):
            return File(file_id=method.file_id, file_unique_id="u", file_path="documents/file.bin").as_(bot)
        if isinstance(method, EditMessageText):
            return True
        return True

    async def stream_content(self, url, headers=None, timeout=30, chunk_size=65536, raise_for_status=True):
        yield self.download_content

    def of(self, method_type):
        return [r for r in self.requests if isinstance(r, method_type)]


def make_bot(bot_username):
    session = MockedSession(bot_username)
    return Bot(token="42:TEST-TOKEN-NOT-REAL", session=session), session


def make_init_data(bot_token, user, start_param):
    """Build Telegram Mini App initData signed like Telegram does."""
    params = {
        "auth_date": str(int(time.time())),
        "start_param": start_param,
        "user": json.dumps(user, separators=(",", ":")),
    }
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    params["hash"] = hmac.new(secret, data_check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode(params)
