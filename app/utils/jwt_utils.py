import datetime

import jwt

from config import JWT_SECRET


def encode_payload(payload):
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def decode_token(token):
    return jwt.decode(token, JWT_SECRET, algorithms="HS256")


def create_token(key: str):
    now = datetime.datetime.utcnow()
    expiration_time = now + datetime.timedelta(hours=24)
    payload = {"key": key, "iat": now, "exp": expiration_time}
    token = encode_payload(payload)
    return token
