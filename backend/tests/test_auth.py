import pytest


@pytest.mark.asyncio
async def test_register_login_me(client) -> None:
    email = "auth-user@example.com"
    # прямая регистрация (собственный /register)
    r = await client.post("/api/auth/register", json={"email": email, "password": "strongpass123"})
    assert r.status_code == 201, r.text

    # вход через фабричный /login
    r = await client.post("/api/auth/login", json={"email": email, "password": "strongpass123"})
    assert r.status_code == 200, r.text
    tokens = r.json()
    assert tokens["access_token"] and tokens["refresh_token"]

    # /me из фабрики
    r = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert r.status_code == 200, r.text
    assert r.json()["email"] == email

    # refresh
    r = await client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200, r.text


@pytest.mark.asyncio
async def test_login_wrong_password(client) -> None:
    await client.post("/api/auth/register", json={"email": "x@example.com", "password": "strongpass123"})
    r = await client.post("/api/auth/login", json={"email": "x@example.com", "password": "wrongpass1"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_auth(client) -> None:
    r = await client.get("/api/auth/me")
    assert r.status_code == 401
