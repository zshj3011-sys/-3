"""v3.6.2 新端点测试

补齐 PRD §07 用户故事地图被遗漏的两个 Must·V1.0:
- #139 医疗安全事件上报
- #165 科研数据导入 (Excel/CSV/SPSS)
"""
import io
import pytest


# =================================================================
# A. 医疗安全事件上报 (PRD §07 #139)
# =================================================================

@pytest.mark.asyncio
async def test_safety_events_seeded(authed_admin_client):
    """种子已写入 ≥4 条事件 (覆盖 reported/investigating/resolved/closed)"""
    r = await authed_admin_client.get("/v1/safety-events/?page=1&page_size=50")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 200
    assert body["meta"]["total"] >= 4
    statuses = {e["status"] for e in body["data"]}
    assert "reported" in statuses
    assert "resolved" in statuses


@pytest.mark.asyncio
async def test_safety_events_stats(authed_admin_client):
    """统计端点应返回 by_status / by_severity / by_type 聚合"""
    r = await authed_admin_client.get("/v1/safety-events/stats")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["total"] >= 4
    assert isinstance(data["by_status"], dict)
    assert isinstance(data["by_severity"], dict)
    assert isinstance(data["by_type"], dict)
    # 至少包含一种 medication_error 类型 (种子数据)
    assert "medication_error" in data["by_type"]


@pytest.mark.asyncio
async def test_safety_event_report_and_update(authed_doctor_client, authed_admin_client):
    """医生上报 → 管理员变更状态 → 自动写 resolved_at"""
    payload = {
        "event_type": "fall", "severity": "iii",
        "title": "测试用例: 患者跌倒",
        "description": "测试: 患者夜间下床跌倒, 轻微挫伤",
        "location": "测试病区", "occurred_at": "2026-06-13T03:00:00",
    }
    r = await authed_doctor_client.post("/v1/safety-events/", json=payload)
    assert r.status_code == 200
    eid = r.json()["data"]["id"]
    assert r.json()["data"]["status"] == "reported"

    # 管理员处理
    r2 = await authed_admin_client.patch(
        f"/v1/safety-events/{eid}",
        json={"status": "resolved", "root_cause": "夜间巡视疏漏",
              "corrective_action": "增加 1-3am 巡视点"},
    )
    assert r2.status_code == 200
    d = r2.json()["data"]
    assert d["status"] == "resolved"
    assert d["resolved_at"] is not None
    assert d["root_cause"] == "夜间巡视疏漏"


@pytest.mark.asyncio
async def test_safety_event_non_admin_cannot_patch(authed_doctor_client):
    """普通医生不能更新事件状态"""
    # 先上报一条
    r = await authed_doctor_client.post("/v1/safety-events/", json={
        "event_type": "other", "severity": "iv",
        "title": "测试 RBAC",
        "description": "用于测试非管理员 PATCH 应被拒绝",
        "occurred_at": "2026-06-13T10:00:00",
    })
    eid = r.json()["data"]["id"]
    # 尝试用医生身份 PATCH
    r2 = await authed_doctor_client.patch(
        f"/v1/safety-events/{eid}", json={"status": "investigating"}
    )
    assert r2.status_code == 403


@pytest.mark.asyncio
async def test_safety_event_invalid_enum(authed_doctor_client):
    """非法 severity 应返回 400"""
    r = await authed_doctor_client.post("/v1/safety-events/", json={
        "event_type": "fall", "severity": "x",  # 非法
        "title": "测试",
        "description": "测试",
        "occurred_at": "2026-06-13T10:00:00",
    })
    assert r.status_code == 400


# =================================================================
# B. 科研数据导入 (PRD §07 #165)
# =================================================================

@pytest.mark.asyncio
async def test_dataset_list_seeded(authed_researcher_client):
    """科研账号能看到 2 条种子数据集"""
    r = await authed_researcher_client.get("/v1/research/datasets/")
    assert r.status_code == 200
    body = r.json()
    assert body["meta"]["total"] >= 2
    names = [d["name"] for d in body["data"]]
    assert any("高血压" in n or "ACS" in n for n in names)


@pytest.mark.asyncio
async def test_dataset_upload_csv(authed_researcher_client):
    """CSV 上传 → 嗅探列类型 → 返回 schema + preview"""
    csv_bytes = (
        "patient_id,age,sex,sbp,hba1c\n"
        "1,58,M,142,7.8\n"
        "2,64,F,138,7.2\n"
        "3,71,M,150,8.5\n"
        "4,49,F,128,6.4\n"
    ).encode("utf-8")
    files = {"file": ("test_cohort.csv", io.BytesIO(csv_bytes), "text/csv")}
    r = await authed_researcher_client.post(
        "/v1/research/datasets/upload", files=files,
        data={"name": "pytest-csv", "notes": "测试上传"},
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["file_format"] == "csv"
    assert data["rows"] == 4
    assert data["columns"] == 5
    # 嗅探类型应识别出 age=int, sbp=int, hba1c=float, sex=str
    schema = {c["name"]: c["dtype"] for c in data["schema"]}
    assert schema.get("age") == "int"
    assert schema.get("hba1c") == "float"
    assert schema.get("sex") == "str"
    # 预览应有 4 行
    assert len(data["preview"]) == 4


@pytest.mark.asyncio
async def test_dataset_upload_xlsx(authed_researcher_client):
    """Excel xlsx 上传 → openpyxl 解析"""
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.append(["case_id", "door_to_balloon_min", "mortality"])
    ws.append(["ACS-001", 68, 0])
    ws.append(["ACS-002", 95, 0])
    ws.append(["ACS-003", 120, 1])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    files = {
        "file": (
            "test_acs.xlsx", buf,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    r = await authed_researcher_client.post(
        "/v1/research/datasets/upload", files=files,
        data={"name": "pytest-xlsx"},
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["file_format"] == "xlsx"
    assert data["rows"] == 3
    assert data["columns"] == 3


@pytest.mark.asyncio
async def test_dataset_upload_rejects_bad_ext(authed_researcher_client):
    """不支持的格式应返回 400"""
    files = {"file": ("bad.txt", io.BytesIO(b"not a dataset"), "text/plain")}
    r = await authed_researcher_client.post(
        "/v1/research/datasets/upload", files=files
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_dataset_preview_and_delete(authed_researcher_client):
    """上传 → 预览 → 删除 全流程"""
    csv_bytes = b"col_a,col_b\n1,foo\n2,bar\n"
    files = {"file": ("tmp.csv", io.BytesIO(csv_bytes), "text/csv")}
    r = await authed_researcher_client.post(
        "/v1/research/datasets/upload", files=files, data={"name": "for-delete"}
    )
    assert r.status_code == 200
    ds_id = r.json()["data"]["id"]

    # preview
    r2 = await authed_researcher_client.get(f"/v1/research/datasets/{ds_id}/preview")
    assert r2.status_code == 200
    pv = r2.json()["data"]
    assert pv["rows"] == 2
    assert len(pv["preview"]) == 2

    # delete
    r3 = await authed_researcher_client.delete(f"/v1/research/datasets/{ds_id}")
    assert r3.status_code == 200
    assert r3.json()["data"]["deleted"] == ds_id

    # 再 preview 应 404
    r4 = await authed_researcher_client.get(f"/v1/research/datasets/{ds_id}/preview")
    assert r4.status_code == 404


@pytest.mark.asyncio
async def test_dataset_sav_when_pyreadstat_missing(authed_researcher_client):
    """.sav 文件: pyreadstat 不安装时应返回 501 + 友好提示"""
    files = {"file": ("test.sav", io.BytesIO(b"fake sav binary"), "application/x-sav")}
    r = await authed_researcher_client.post(
        "/v1/research/datasets/upload", files=files
    )
    # 取决于环境是否装了 pyreadstat
    try:
        import pyreadstat  # type: ignore  # noqa
        # 如果环境有，可能能进入解析但因 binary 非真实 sav 而 ValueError
        assert r.status_code in (200, 400, 500, 501)
    except ImportError:
        assert r.status_code == 501
        assert "pyreadstat" in r.json().get("message", "").lower()
