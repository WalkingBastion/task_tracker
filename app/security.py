import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt

from app.config import get_settings

PBKDF2_ITERATIONS = 260_000


def _derive(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = _derive(password, salt)
    return f"{base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_b64, digest_b64 = stored.split("$", 1)
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
    except ValueError:
        return False
    return hmac.compare_digest(_derive(password, salt), expected)


DUMMY_HASH = hash_password("dummy-password-for-timing")


def create_access_token(subject: str) -> str:
    settings = get_settings()
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "exp": expires}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> str:
    settings = get_settings()
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise jwt.InvalidTokenError("missing subject")
    return subject
