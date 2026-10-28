import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.main import app


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(
        bind=engine, expire_on_commit=False
    )

    def override_db():
        with TestingSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_db

    try:
        with TestClient(app) as test_client:
            yield test_client
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
    response = client.post(
        "/api/v1/orders", json=sample_order()
    )
    assert response.status_code == 201
    assert response.json()["total_cents"] == 2500
    assert response.json()["status"] == "pending"


def test_list_and_get_order(client):
    created = client.post(
        "/api/v1/orders", json=sample_order()
    ).json()
    listed = client.get("/api/v1/orders")
    fetched = client.get(
        f"/api/v1/orders/{created['id']}"
    )

    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert fetched.json()["id"] == created["id"]


def test_reject_empty_items(client):
    payload = {
        "customer_name": "Demo Customer",
        "items": [],
    }
    response = client.post("/api/v1/orders", json=payload)
    assert response.status_code == 422


def test_reject_negative_price(client):
    payload = sample_order()
    payload["items"][0]["unit_price_cents"] = -1
    response = client.post("/api/v1/orders", json=payload)
    assert response.status_code == 422


def test_status_transition(client):
    created = client.post(
        "/api/v1/orders", json=sample_order()
    ).json()
    url = f"/api/v1/orders/{created['id']}/status"

    confirmed = client.patch(
        url, json={"status": "confirmed"}
    )
    assert confirmed.status_code == 200

    invalid = client.patch(
        url, json={"status": "cancelled"}
    )
    assert invalid.status_code == 409


def test_missing_order(client):
    response = client.get("/api/v1/orders/999999")
    assert response.status_code == 404
