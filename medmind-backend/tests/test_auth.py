"""认证相关测试"""
import pytest


@pytest.mark.asyncio
async def test_login_success(client):
    r = await client.post("/v1/auth/login", json={"username": "dr_zhang", "password": "doctor123"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert "access_token" in data
    assert data["user"]["role"] == "doctor"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    # 使用足够长的错误密码 (绕过 schema 长度校验)
    r = await client.post("/v1/auth/login", json={"username": "dr_zhang", "password": "wrongpw123"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_login_invalid_schema(client):
    # 太短的密码 → 422 schema 验证失败
    r = await client.post("/v1/auth/login", json={"username": "x", "password": "a"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_me_with_token(client, auth_headers):
    r = await client.get("/v1/auth/me", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["data"]["username"] == "dr_zhang"


@pytest.mark.asyncio
async def test_me_without_token(client):
    r = await client.get("/v1/auth/me")
    assert r.status_code == 401
