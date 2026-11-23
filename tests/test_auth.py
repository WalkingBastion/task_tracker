from app.security import hash_password, verify_password


def test_register_success(client):
    response = client.post(
        "/auth/register",
        json={"username": "ivan", "full_name": "Иван Иванов", "password": "Password123"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "ivan"
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_duplicate(client):
    payload = {"username": "ivan", "full_name": "Иван", "password": "Password123"}
    assert client.post("/auth/register", json=payload).status_code == 201
    assert client.post("/auth/register", json=payload).status_code == 409


def test_register_short_password(client):
    response = client.post(
        "/auth/register",
        json={"username": "ivan", "full_name": "Иван", "password": "short"},
    )
    assert response.status_code == 422


def test_register_invalid_username(client):
    response = client.post(
        "/auth/register",
        json={"username": "bad name'; --", "full_name": "Иван", "password": "Password123"},
    )
    assert response.status_code == 422


def test_login_success_and_me(client, alice):
    _, headers = alice
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["username"] == "alice"


def test_login_wrong_password(client, alice):
    response = client.post("/auth/login", json={"username": "alice", "password": "wrong-password"})
    assert response.status_code == 401


def test_login_unknown_user(client):
    response = client.post("/auth/login", json={"username": "ghost", "password": "Password123"})
    assert response.status_code == 401


def test_login_sql_injection_payload(client, alice):
    response = client.post(
        "/auth/login",
        json={"username": "alice' OR '1'='1", "password": "' OR '1'='1"},
    )
    assert response.status_code == 401


def test_protected_endpoints_require_token(client):
    for path in ("/tasks", "/topics", "/users", "/analytics/summary", "/auth/me"):
        assert client.get(path).status_code == 401


def test_invalid_token_rejected(client):
    response = client.get("/tasks", headers={"Authorization": "Bearer not-a-token"})
    assert response.status_code == 401


def test_health_is_public(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_password_hashing():
    stored = hash_password("Password123")
    assert stored != "Password123"
    assert verify_password("Password123", stored)
    assert not verify_password("password123", stored)
    assert hash_password("Password123") != stored
    assert not verify_password("Password123", "broken-value")
