import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, hash_password
from app.db.database import Base, get_db
from app.main import app
from app.models.user import User


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

    with TestingSession() as session:
        regular = User(
            email="user@example.com",
            password_hash=hash_password("UserPassword123!"),
            role="user",
            is_active=True,
        )
        admin = User(
            email="admin@example.com",
            password_hash=hash_password("AdminPassword123!"),
            role="admin",
            is_active=True,
        )
        session.add_all([regular, admin])
        session.commit()
        session.refresh(regular)
        session.refresh(admin)

        user_id = regular.id
        admin_id = admin.id

    user_headers = {
        "Authorization": f"Bearer {create_access_token(str(user_id))}"
    }
    admin_headers = {
        "Authorization": f"Bearer {create_access_token(str(admin_id))}"
    }

    def override_db():
        with TestingSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_db

    try:
        with TestClient(app) as http:
            yield http, user_headers, admin_headers
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def sample_order():
    return {
        "customer_name": "Demo Customer",
        "items": [
            {
                "product_name": "Coffee",
                "quantity": 2,
                "unit_price_cents": 1250,
            }
        ],
    }


def test_create_order(client):
    http, user, _ = client
    response = http.post(
        "/api/v1/orders", json=sample_order(), headers=user
    )
    assert response.status_code == 201
    assert response.json()["total_cents"] == 2500
    assert response.json()["status"] == "pending"


def test_list_and_get_order(client):
    http, user, _ = client
    created = http.post(
        "/api/v1/orders", json=sample_order(), headers=user
    ).json()
    listed = http.get("/api/v1/orders", headers=user)
    fetched = http.get(
        f"/api/v1/orders/{created['id']}", headers=user
    )

    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert fetched.status_code == 200
    assert fetched.json()["id"] == created["id"]


def test_reject_empty_items(client):
    http, user, _ = client
    payload = {
        "customer_name": "Demo Customer",
        "items": [],
    }
    response = http.post(
        "/api/v1/orders", json=payload, headers=user
    )
    assert response.status_code == 422


def test_reject_negative_price(client):
    http, user, _ = client
    payload = sample_order()
    payload["items"][0]["unit_price_cents"] = -1
    response = http.post(
        "/api/v1/orders", json=payload, headers=user
    )
    assert response.status_code == 422


def test_status_transition(client):
    http, user, admin = client
    created = http.post(
        "/api/v1/orders", json=sample_order(), headers=user
    ).json()
    url = f"/api/v1/orders/{created['id']}/status"

    confirmed = http.patch(
        url, json={"status": "confirmed"}, headers=admin
    )
    assert confirmed.status_code == 200

    invalid = http.patch(
        url, json={"status": "cancelled"}, headers=admin
    )
    assert invalid.status_code == 409


def test_missing_order(client):
    http, user, _ = client
    response = http.get(
        "/api/v1/orders/999999", headers=user
    )
    assert response.status_code == 404


@pytest.mark.parametrize(
    "method,path,payload",
    [
        ("POST", "/api/v1/orders", sample_order()),
        ("GET", "/api/v1/orders", None),
        ("GET", "/api/v1/orders/1", None),
        ("PATCH", "/api/v1/orders/1/status", {"status": "confirmed"}),
    ],
)
def test_orders_require_authentication(client, method, path, payload):
    http, _, _ = client
    response = http.request(method, path, json=payload)
    assert response.status_code == 401


def test_invalid_token_rejected(client):
    http, _, _ = client
    response = http.get(
        "/api/v1/orders",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401


def test_regular_user_cannot_update_status(client):
    http, user, _ = client
    created = http.post(
        "/api/v1/orders", json=sample_order(), headers=user
    ).json()

    response = http.patch(
        f"/api/v1/orders/{created['id']}/status",
        json={"status": "confirmed"},
        headers=user,
    )

    assert response.status_code == 403

    unchanged = http.get(
        f"/api/v1/orders/{created['id']}", headers=user
    )
    assert unchanged.status_code == 200
    assert unchanged.json()["status"] == "pending"


def test_admin_can_create_and_list_orders(client):
    http, _, admin = client
    created = http.post(
        "/api/v1/orders", json=sample_order(), headers=admin
    )
    assert created.status_code == 201

    listed = http.get("/api/v1/orders", headers=admin)
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_health_remains_public(client):
    http, _, _ = client
    response = http.get("/health")
    assert response.status_code == 200
