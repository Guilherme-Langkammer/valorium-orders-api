from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


@pytest.fixture(autouse=True)
def jwt_secret(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-only-secret-key-with-at-least-32-bytes",
    )


def test_password_hash_and_verify():
    password = "A-Strong-Test-Password-123!"
    encoded = hash_password(password)

    assert encoded.startswith("$argon2id$")
    assert password not in encoded
    assert verify_password(password, encoded)
    assert not verify_password("wrong-password", encoded)
    assert not verify_password(password, "invalid-hash")


def test_create_and_decode_access_token():
    token = create_access_token("user-123")

    assert decode_access_token(token) == "user-123"


def test_reject_tampered_token():
    token = create_access_token("user-123")
    modified = token[:-2] + "xx"

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(modified)


def test_reject_expired_token():
    from app.core.security import get_jwt_secret

    expired = jwt.encode(
        {
            "sub": "user-123",
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        },
        get_jwt_secret(),
        algorithm="HS256",
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(expired)


def test_reject_missing_secret(monkeypatch):
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError):
        create_access_token("user-123")