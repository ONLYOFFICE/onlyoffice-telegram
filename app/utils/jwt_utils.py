import jwt

from config import JWT_SECRET


def encode_payload(payload):
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def decode_token(token):
    return jwt.decode(token, JWT_SECRET, algorithms="HS256")
