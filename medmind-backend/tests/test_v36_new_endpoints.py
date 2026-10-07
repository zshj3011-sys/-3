"""v3.6 新端点测试 — 挂号 / 消息通知 / PRD 字面路径对齐"""
import pytest


@pytest.mark.asyncio
async def test_prd_generate_note_alias(authed_doctor_client):
    """PRD §5.1: POST /ai/consultation/generate-note (字面路径)"""
    r = await authed_doctor_client.post(
        "/v1/ai/consultation/generate-note",
        json={"patient_id": 1, "transcript": "胸痛 3 天, 放射至左肩"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["code"] == 200


@pytest.mark.asyncio
async def test_prd_pre_consultation_path_param(client):
    """PRD §4.2: POST /ai/pre-consultation/{session_id}/message (路径参数式)"""
    # 启动会话
    r = await client.post("/v1/ai/pre-consultation/start", json={"chief_complaint": "头痛"})
    assert r.status_code == 200
    sid = r.json()["data"]["session_id"]

    # 用 PRD 路径参数形式发消息
    r2 = await client.post(
        f"/v1/ai/pre-consultation/{sid}/message",
        json={"session_id": sid, "message": "头痛 3 天, 太阳穴位置"},
    )
    assert r2.status_code == 200
    assert r2.json()["code"] == 200


@pytest.mark.asyncio
async def test_appointments_list(authed_doctor_client):
    """v3.6: GET /v1/appointments — 返回种子的 5 条预约"""
    r = await authed_doctor_client.get("/v1/appointments/?page=1&size=10")
    assert r.status_code == 200
    data = r.json()
    assert data["code"] == 200
    assert data["meta"]["total"] >= 5
    items = data["data"]
    assert len(items) >= 5
    assert all("patient_name" in x for x in items)


@pytest.mark.asyncio
async def test_appointments_slots(authed_doctor_client):
    """v3.6: GET /v1/appointments/slots — 返回可用号源"""
    r = await authed_doctor_client.get("/v1/appointments/slots")
    assert r.status_code == 200
    data = r.json()
    assert data["code"] == 200
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0
    first = data["data"][0]
    assert "doctor_name" in first and "remaining" in first


@pytest.mark.asyncio
async def test_appointments_today_doctor(authed_doctor_client):
    """v3.6: GET /v1/appointments/today (用户故事 #86)"""
    r = await authed_doctor_client.get("/v1/appointments/today")
    assert r.status_code == 200
    data = r.json()
    assert data["code"] == 200


@pytest.mark.asyncio
async def test_notifications_list_for_patient(authed_patient_client):
    """v3.6: GET /v1/notifications — 患者应有 4 条种子消息"""
    r = await authed_patient_client.get("/v1/notifications/")
    assert r.status_code == 200
    data = r.json()
    assert data["code"] == 200
    assert data["meta"]["total"] >= 4
    items = data["data"]
    assert any("预约提醒" in x["title"] or "用药提醒" in x["title"] for x in items)


@pytest.mark.asyncio
async def test_notifications_unread_count(authed_patient_client):
    """v3.6: GET /v1/notifications/unread-count"""
    r = await authed_patient_client.get("/v1/notifications/unread-count")
    assert r.status_code == 200
    data = r.json()
    assert data["code"] == 200
    assert data["data"]["total"] >= 4
    assert isinstance(data["data"]["by_category"], dict)


@pytest.mark.asyncio
async def test_notifications_mark_read(authed_patient_client):
    """v3.6: PATCH /v1/notifications/{id}/read"""
    # 先列表拿 id
    r = await authed_patient_client.get("/v1/notifications/")
    items = r.json()["data"]
    assert items
    nid = items[0]["id"]

    r2 = await authed_patient_client.patch(f"/v1/notifications/{nid}/read")
    assert r2.status_code == 200
    assert r2.json()["data"]["is_read"] is True


@pytest.mark.asyncio
async def test_appointment_create_and_cancel(authed_doctor_client):
    """v3.6: POST + PATCH /cancel 创建并取消预约"""
    from datetime import datetime, timedelta
    future = (datetime.now() + timedelta(days=7)).replace(hour=10, minute=0, second=0, microsecond=0)

    r = await authed_doctor_client.post("/v1/appointments/", json={
        "patient_id": 1,
        "doctor_id": 1,
        "scheduled_at": future.isoformat(),
        "visit_type": "outpatient",
        "chief_complaint": "测试预约",
    })
    assert r.status_code == 200, r.text
    appt_id = r.json()["data"]["id"]

    r2 = await authed_doctor_client.patch(f"/v1/appointments/{appt_id}/cancel")
    assert r2.status_code == 200
    assert r2.json()["data"]["status"] == "cancelled"
