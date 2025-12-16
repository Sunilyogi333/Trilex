from datetime import datetime, timedelta
import jwt
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed

JWT_SECRET = settings.JWT_SECRET


def create_secure_token(payload: dict, minutes: int = 30) -> str:
    payload["exp"] = datetime.utcnow() + timedelta(minutes=minutes)
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def decode_secure_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except Exception:
        raise AuthenticationFailed("Invalid or expired token.")
