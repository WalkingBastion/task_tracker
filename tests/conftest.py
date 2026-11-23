import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret-key-test-secret-key-0123456789"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def register_and_login(client, username, password="Password123"):
    response = client.post(
        "/auth/register",
        json={"username": username, "full_name": username.capitalize(), "password": password},
    )
    assert response.status_code == 201
    user = response.json()
    token = client.post("/auth/login", json={"username": username, "password": password})
    assert token.status_code == 200
    headers = {"Authorization": f"Bearer {token.json()['access_token']}"}
    return user, headers


@pytest.fixture()
def alice(client):
    return register_and_login(client, "alice")


@pytest.fixture()
def bob(client):
    return register_and_login(client, "bob")
