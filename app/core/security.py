import os
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def get_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET_KEY", "")

    if len(secret.encode("utf-8")) < 32:
        raise RuntimeError(
            "JWT_SECRET_KEY must contain at least 32 UTF-8 bytes"
        )

    return secret


def create_access_token(subject: str) -> str:
    if not subject:
        raise ValueError("Token subject is required")

    now = datetime.now(timezone.utc)

    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }

    return jwt.encode(
        payload,
        get_jwt_secret(),
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str) -> str:
    payload = jwt.decode(
        token,
        get_jwt_secret(),
        algorithms=[ALGORITHM],
        options={"require": ["sub", "iat", "exp"]},
    )

    subject = payload.get("sub")

    if not isinstance(subject, str) or not subject:
        raise jwt.InvalidTokenError("Invalid token subject")

    return subject