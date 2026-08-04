import base64
import hashlib
import json
import random
import time
import uuid

import blackboxprotobuf
import msgpack


def trans_cookies(cookies_str):
    cookies = {}
    for i in cookies_str.split("; "):
        try:
            cookies[i.split("=")[0]] = "=".join(i.split("=")[1:])
        except Exception:
            continue
    return cookies


def trans_cookies_str(cookies_dict):
    cookies_str = ""
    for key, value in cookies_dict.items():
        cookies_str += f"{key}={value}; "
    return cookies_str[:-2]


def get_session_cookies(session):
    return session.cookies.get_dict()


def get_session_cookies_str(session):
    cookies = session.cookies.get_dict()
    cookies_str = ""
    for key, value in cookies.items():
        cookies_str += f"{key}={value}; "
    return cookies_str[:-2]


def generate_mid():
    return f"{random.randint(0, 999)}{int(time.time() * 1000)} 0"


def generate_uuid():
    return f"-{int(time.time() * 1000)}1"


def generate_device_id(user_id):
    return f"{uuid.uuid4()}-{user_id}"


_SIGN_SALT = "34839810"


def generate_sign(t, token, data):
    msg = f"{token}&{t}&{_SIGN_SALT}&{data}"
    return hashlib.md5(msg.encode("utf-8")).hexdigest()


def decrypt(data):
    raw = base64.b64decode(data)
    unpacked = msgpack.unpackb(raw, raw=False, strict_map_key=False)
    return json.dumps(unpacked, ensure_ascii=False, default=str)

