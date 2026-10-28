import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.main import app
from app.models.user import User
from app.core.security import verify_password


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-only-secret-key-with-at-least-32-bytes",
    )

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    TestingSession = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    def override_db():
        with TestingSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_db

    try:
        with TestClient(app) as test_client:
            yield test_client, TestingSession
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_register_user(client):
    http, session_factory = client

    response = http.post(
        "/api/v1/auth/register",
        json={
            "email": " Demo@Example.com ",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == "demo@example.com"
    assert response.json()["role"] == "user"
    assert "password_hash" not in response.json()

    with session_factory() as session:
        user = session.query(User).one()
        assert verify_password("StrongPassword123!", user.password_hash)


def test_duplicate_email(client):
    http, _ = client

    payload = {
        "email": "demo@example.com",
        "password": "StrongPassword123!",
    }

    assert http.post("/api/v1/auth/register", json=payload).status_code == 201
    assert http.post("/api/v1/auth/register", json=payload).status_code == 409


def test_public_registration_cannot_choose_admin(client):
    http, _ = client

    response = http.post(
        "/api/v1/auth/register",
        json={
            "email": "demo@example.com",
            "password": "StrongPassword123!",
            "role": "admin",
        },
    )

    assert response.status_code == 422


def test_login_and_me(client):
    http, _ = client

    http.post(
        "/api/v1/auth/register",
        json={
            "email": "demo@example.com",
            "password": "StrongPassword123!",
        },
    )

    login = http.post(
        "/api/v1/auth/login",
        json={
            "email": "DEMO@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert login.status_code == 200
    token = login.json()["access_token"]

    response = http.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "demo@example.com"


def test_invalid_password(client):
    http, _ = client

    http.post(
        "/api/v1/auth/register",
        json={
            "email": "demo@example.com",
            "password": "StrongPassword123!",
        },
    )

    response = http.post(
        "/api/v1/auth/login",
        json={
            "email": "demo@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401


def test_me_without_token(client):
    http, _ = client

    assert http.get("/api/v1/auth/me").status_code == 401


def test_me_invalid_token(client):
    http, _ = client

    response = http.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401


def test_inactive_user_cannot_login(client):
    http, session_factory = client

    http.post(
        "/api/v1/auth/register",
        json={
            "email": "demo@example.com",
            "password": "StrongPassword123!",
        },
    )

    with session_factory() as session:
        user = session.query(User).one()
        user.is_active = False
        session.commit()

    response = http.post(
        "/api/v1/auth/login",
        json={
            "email": "demo@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 401