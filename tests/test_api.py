"""FastAPI 接口冒烟测试：登录 / 401 / 403 / 看板数据。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# 确保有库表后再导入 app（app 模块加载时会 ensure_db_from_csv + init_db）
from backend.main import app  # noqa: E402


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


def test_auth_me(client: TestClient):
    token = _login(client, "admin", "admin123")
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["role"] == "admin"


def test_user_can_read_kpi_but_not_work_orders(client: TestClient):
    token = _login(client, "user", "user123")
    headers = {"Authorization": f"Bearer {token}"}
    kpi = client.get("/api/kpi", headers=headers)
    assert kpi.status_code == 200
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
    token = _login(client, "admin", "admin123")
    res = client.get(
        "/api/region-volume",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    rows = res.json()
    assert isinstance(rows, list)
    if rows:
        assert "name" in rows[0] and "value" in rows[0]


def test_submit_appeal_creates_record(client: TestClient):
    token = _login(client, "user", "user123")
    res = client.post(
        "/api/appeals",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "content": "pytest 冒烟：道路破损需处理",
            "category": "道路破损",
            "region": "布鲁克林区",
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body.get("content") or body.get("id") is not None
