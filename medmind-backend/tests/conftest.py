"""pytest 公共 fixtures"""
import os
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# 切换到独立测试库
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_medmind.db"
os.environ["DEMO_MODE"] = "true"
os.environ["LLM_PROVIDER"] = "mock"

from app.main import app  # noqa: E402
from app.core.database import init_db, AsyncSessionLocal  # noqa: E402
from scripts.seed import seed_all  # noqa: E402


@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def _setup_db():
    # 删除旧测试库
    if os.path.exists("test_medmind.db"):
        os.unlink("test_medmind.db")
    await init_db()
    async with AsyncSessionLocal() as db:
        await seed_all(db)
        await db.commit()
    yield


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def doctor_token(client):
    r = await client.post("/v1/auth/login",
                          json={"username": "dr_zhang", "password": "doctor123"})
    return r.json()["data"]["access_token"]


@pytest_asyncio.fixture
async def auth_headers(doctor_token):
    return {"Authorization": f"Bearer {doctor_token}"}


# ===== v3.6 新增 fixtures =====
@pytest_asyncio.fixture
async def authed_doctor_client():
    """已用医生身份认证的 client"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post("/v1/auth/login",
                         json={"username": "dr_zhang", "password": "doctor123"})
        token = r.json()["data"]["access_token"]
        c.headers["Authorization"] = f"Bearer {token}"
        yield c


@pytest_asyncio.fixture
async def authed_patient_client():
    """已用患者身份认证的 client"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post("/v1/auth/login",
                         json={"username": "patient_li", "password": "patient123"})
        token = r.json()["data"]["access_token"]
        c.headers["Authorization"] = f"Bearer {token}"
        yield c


@pytest_asyncio.fixture
async def authed_admin_client():
    """已用管理员身份认证的 client (v3.6.2)"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post("/v1/auth/login",
                         json={"username": "admin", "password": "admin123"})
        token = r.json()["data"]["access_token"]
        c.headers["Authorization"] = f"Bearer {token}"
        yield c


@pytest_asyncio.fixture
async def authed_researcher_client():
    """已用科研者身份认证的 client (v3.6.2)"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post("/v1/auth/login",
                         json={"username": "prof_zhao", "password": "researcher123"})
        token = r.json()["data"]["access_token"]
        c.headers["Authorization"] = f"Bearer {token}"
        yield c
