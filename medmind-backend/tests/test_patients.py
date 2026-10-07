"""患者管理测试"""
import pytest


@pytest.mark.asyncio
async def test_list_patients(client, auth_headers):
    r = await client.get("/v1/patients/", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["meta"]["total"] >= 5
    # 确保 age 字段被正确填充
    for p in body["data"]:
        assert "age" in p


@pytest.mark.asyncio
async def test_get_patient_detail(client, auth_headers):
    r = await client.get("/v1/patients/1", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["data"]["real_name"]


@pytest.mark.asyncio
async def test_search_patients(client, auth_headers):
    r = await client.get("/v1/patients/?keyword=李", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["meta"]["total"] >= 1
