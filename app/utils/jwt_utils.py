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

import datetime

import jwt

from config import JWT_SECRET, TTL


def encode_payload(payload):
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def decode_token(token):
    return jwt.decode(token, JWT_SECRET, algorithms="HS256")


def create_token(key: str):
    now = datetime.datetime.utcnow()
    expiration_time = now + datetime.timedelta(hours=TTL)
    payload = {"key": key, "iat": now, "exp": expiration_time}
    token = encode_payload(payload)
    return token
