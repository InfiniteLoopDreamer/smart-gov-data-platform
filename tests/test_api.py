"""FastAPI 接口冒烟测试：登录 / 401 / 403 / 看板数据。"""

from __future__ import annotations

import sys
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# 确保有库表后再导入 app（app 模块加载时会 ensure_db_from_csv + init_db）
from backend.main import app  # noqa: E402
from shared import database  # noqa: E402


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def _login(client: TestClient, username: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    data = res.json()
    assert "token" in data
    assert data["user"]["username"] == username
    return data["token"]


def test_health_public(client: TestClient):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] in ("ok", "error")


def test_login_success_admin(client: TestClient):
    token = _login(client, "admin", "admin123")
    assert token


def test_login_wrong_password(client: TestClient):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert res.status_code == 401


def test_protected_without_token_401(client: TestClient):
    res = client.get("/api/dashboard/stats")
    assert res.status_code == 401


def test_protected_with_bad_token_401(client: TestClient):
    res = client.get("/api/dashboard/stats", headers={"Authorization": "Bearer invalid.token"})
    assert res.status_code == 401


def test_admin_can_read_dashboard(client: TestClient):
    token = _login(client, "admin", "admin123")
    res = client.get("/api/dashboard/stats", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    body = res.json()
    assert "stats" in body
    assert "regionData" in body
    assert body.get("total", 0) >= 0
    assert body["stats"][0]["trendLabel"] == "近7日环比"
    assert body["stats"][3]["trend"] is None


def test_user_forbidden_on_users_api(client: TestClient):
    token = _login(client, "user", "user123")
    res = client.get("/api/users", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


def test_admin_can_list_users(client: TestClient):
    token = _login(client, "admin", "admin123")
    res = client.get("/api/users", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    users = res.json()
    assert isinstance(users, list)
    assert any(u.get("username") == "admin" for u in users)


def test_admin_user_management_persists_and_revokes_access(client: TestClient):
    admin_token = _login(client, "admin", "admin123")
    headers = {"Authorization": f"Bearer {admin_token}"}
    username = "pytest_managed_user"
    conn = sqlite3.connect(database.DB_PATH)
    conn.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    try:
        created = client.post(
            "/api/users",
            headers=headers,
            json={
                "username": username,
                "password": "pytest123",
                "name": "接口测试用户",
                "role": "staff",
                "department": "市交通运输局",
            },
        )
        assert created.status_code == 200, created.text
        user_id = created.json()["id"]
        user_token = _login(client, username, "pytest123")

        disabled = client.patch(
            f"/api/users/{user_id}",
            headers=headers,
            json={
                "name": "接口测试用户",
                "role": "staff",
                "department": "市交通运输局",
                "active": False,
            },
        )
        assert disabled.status_code == 200, disabled.text
        assert disabled.json()["active"] == 0
        denied = client.get("/api/auth/me", headers={"Authorization": f"Bearer {user_token}"})
        assert denied.status_code == 401
    finally:
        conn = sqlite3.connect(database.DB_PATH)
        conn.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        conn.close()


def test_auth_me(client: TestClient):
    token = _login(client, "admin", "admin123")
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["role"] == "admin"


def test_staff_login_contains_bound_department_and_only_sees_own_orders(client: TestClient):
    token = _login(client, "traffic_staff", "staff123")
    headers = {"Authorization": f"Bearer {token}"}
    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["department"] == "市交通运输局"
    orders = client.get("/api/work-orders", headers=headers)
    assert orders.status_code == 200
    assert all(item["department"] == "市交通运输局" for item in orders.json())


def test_staff_registration_requires_valid_department(client: TestClient):
    res = client.post(
        "/api/auth/register",
        json={
            "username": "pytest_no_dept",
            "password": "staff123",
            "name": "测试",
            "role": "staff",
            "staff_code": "demo-staff-2026",
        },
    )
    assert res.status_code == 400
    assert "所属部门" in res.json()["detail"]


def test_user_cannot_read_admin_analytics_or_work_orders(client: TestClient):
    token = _login(client, "user", "user123")
    headers = {"Authorization": f"Bearer {token}"}
    kpi = client.get("/api/kpi", headers=headers)
    assert kpi.status_code == 403
    wo = client.get("/api/work-orders", headers=headers)
    assert wo.status_code == 403


def test_admin_work_orders_summary(client: TestClient):
    token = _login(client, "admin", "admin123")
    res = client.get(
        "/api/work-orders/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert "total" in body or "finished" in body or isinstance(body, dict)


def test_region_volume_authenticated(client: TestClient):
    token = _login(client, "user", "user123")
    res = client.get(
        "/api/region-volume",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    rows = res.json()
    assert isinstance(rows, list)
    if rows:
        assert "name" in rows[0] and "value" in rows[0]


def test_user_can_read_form_options(client: TestClient):
    token = _login(client, "user", "user123")
    headers = {"Authorization": f"Bearer {token}"}
    categories = client.get("/api/service-categories", headers=headers)
    regions = client.get("/api/region-volume", headers=headers)
    assert categories.status_code == 200
    assert regions.status_code == 200
    assert len(categories.json()) == 6 and regions.json()
    assert all(item.get("department") for item in categories.json())


def test_service_guides_have_unique_titles(client: TestClient):
    token = _login(client, "user", "user123")
    res = client.get(
        "/api/service-guides",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    guides = res.json()
    titles = [item["title"] for item in guides]
    assert len(titles) == len(set(titles))
    assert len(guides) == 6
    assert sum(item["count"] for item in guides) == 50_000
    traffic = next(item for item in guides if item["title"] == "交通出行")
    assert traffic["department"] == "市交通运输局"


def test_submit_appeal_creates_record(client: TestClient):
    token = _login(client, "user", "user123")
    res = client.post(
        "/api/appeals",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "content": "pytest 冒烟：道路破损需处理",
            "category": "市容环境",
            "region": "布鲁克林区",
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body.get("content") or body.get("id") is not None
    appeal_id = body["id"]
    with sqlite3.connect(database.DB_PATH) as conn:
        order = conn.execute(
            "SELECT id, status, department FROM work_orders WHERE source = 'citizen' AND source_id = ?",
            (appeal_id,),
        ).fetchone()
        order_id = order[0]
        assert order[1:] == ("已分派", "市城市管理局")

    staff_token = _login(client, "city_staff", "staff123")
    transition = client.patch(
        f"/api/work-orders/{order_id}",
        headers={"Authorization": f"Bearer {staff_token}"},
        json={"action": "办理", "handler": "测试办理员"},
    )
    assert transition.status_code == 200, transition.text
    assert transition.json()["status"] == "办理中"

    finished = client.patch(
        f"/api/work-orders/{order_id}",
        headers={"Authorization": f"Bearer {staff_token}"},
        json={"action": "办结", "satisfaction": 5},
    )
    assert finished.status_code == 200, finished.text
    assert finished.json()["status"] == "已办结"

    with sqlite3.connect(database.DB_PATH) as conn:
        conn.execute(
            "DELETE FROM work_orders WHERE source = 'citizen' AND source_id = ?",
            (appeal_id,),
        )
        conn.execute("DELETE FROM citizen_appeals WHERE id = ?", (appeal_id,))
        conn.commit()


def test_admin_only_intervenes_for_emergency_orders(client: TestClient):
    user_token = _login(client, "user", "user123")
    created = client.post(
        "/api/appeals",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "content": "pytest 紧急冒烟：道路存在即时安全风险",
            "category": "交通出行",
            "region": "曼哈顿区",
            "priority": "紧急",
        },
    )
    assert created.status_code == 200, created.text
    appeal_id = created.json()["id"]
    with sqlite3.connect(database.DB_PATH) as conn:
        order_id = conn.execute(
            "SELECT id FROM work_orders WHERE source='citizen' AND source_id=?", (appeal_id,)
        ).fetchone()[0]

    admin_token = _login(client, "admin", "admin123")
    reassigned = client.patch(
        f"/api/work-orders/{order_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "action": "紧急改派",
            "department": "市公安局",
            "intervention_note": "涉及即时安全风险，需公安协同",
        },
    )
    assert reassigned.status_code == 200, reassigned.text
    assert reassigned.json()["department"] == "市公安局"
    assert reassigned.json()["assignment_mode"] == "紧急改派"

    with sqlite3.connect(database.DB_PATH) as conn:
        conn.execute("DELETE FROM work_orders WHERE source='citizen' AND source_id=?", (appeal_id,))
        conn.execute("DELETE FROM citizen_appeals WHERE id=?", (appeal_id,))
        conn.commit()
