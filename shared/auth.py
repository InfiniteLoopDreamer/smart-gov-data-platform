"""
认证模块：密码哈希（PBKDF2）+ 签名令牌（HMAC）+ 用户表管理。

使用 Python 标准库实现，无第三方依赖：
- 密码：hashlib.pbkdf2_hmac（加盐，10 万次迭代）
- 令牌：HMAC-SHA256 签名 + 过期时间（简化版 JWT）
- 存储：SQLite users 表（data/gov_data.db）

预置账号：管理员、普通用户和部门人员各一组演示账号。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from pathlib import Path

from shared.catalog import DEPARTMENTS

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "gov_data.db"
SECRET = os.getenv("SMART_GOV_SECRET", "smart-gov-demo-secret-please-change")
TOKEN_TTL = 24 * 3600  # 令牌有效期（秒）

SEED_USERS = [
    ("admin", "admin123", "admin", "系统管理员", "信息中心"),
    ("user", "user123", "user", "普通用户", ""),
    ("traffic_staff", "staff123", "staff", "交通部门人员", "市交通运输局"),
    ("city_staff", "staff123", "staff", "城管部门人员", "市城市管理局"),
]


def get_conn() -> sqlite3.Connection:
    """建立 SQLite 连接（返回 Row 以便按列名访问）。"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# 密码哈希
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    """加盐 PBKDF2 哈希，返回 'salt$hexdigest'。"""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"{salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """校验密码与存储的哈希是否匹配（恒定时间比较）。"""
    try:
        salt, hexdigest = stored.split("$", 1)
    except ValueError:
        return False
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return hmac.compare_digest(dk.hex(), hexdigest)


# ---------------------------------------------------------------------------
# 令牌
# ---------------------------------------------------------------------------
def create_token(payload: dict) -> str:
    """生成 HMAC 签名的令牌，格式：base64(payload).signature。"""
    payload = {**payload, "exp": int(time.time()) + TOKEN_TTL}
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    sig = hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def decode_token(token: str) -> dict:
    """校验并解析令牌，失败抛 ValueError。"""
    try:
        body, sig = token.split(".", 1)
    except ValueError:
        raise ValueError("令牌格式错误")
    expected = hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        raise ValueError("签名校验失败")
    padding = "=" * (-len(body) % 4)
    payload = json.loads(base64.urlsafe_b64decode(body + padding))
    if payload.get("exp", 0) < time.time():
        raise ValueError("令牌已过期")
    return payload


# ---------------------------------------------------------------------------
# 用户管理
# ---------------------------------------------------------------------------
def init_db() -> None:
    """建 users 表并预置管理员/普通用户账号（幂等）。"""
    conn = get_conn()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                name TEXT NOT NULL,
                department TEXT,
                created_at TEXT,
                active INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        cols = [r["name"] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
        if "active" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN active INTEGER NOT NULL DEFAULT 1")
        for username, password, role, name, dept in SEED_USERS:
            exists = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone()
            if not exists:
                conn.execute(
                    "INSERT INTO users (username, password_hash, role, name, department, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (username, hash_password(password), role, name, dept, time.strftime("%Y-%m-%d %H:%M:%S")),
                )
        # 兼容旧演示库：群众账号不应保留历史“办件中心”部门。
        conn.execute("UPDATE users SET department='' WHERE role='user' AND department='办件中心'")
        conn.commit()
    finally:
        conn.close()


def register_user(username: str, password: str, name: str, department: str = "", role: str = "user") -> dict:
    """注册用户，用户名已存在时抛 ValueError。"""
    if role not in {"user", "staff"}:
        raise ValueError("注册角色仅支持群众或部门人员")
    if role == "staff" and department not in DEPARTMENTS:
        raise ValueError("部门人员必须选择有效的所属部门")
    if role == "user":
        department = ""
    conn = get_conn()
    try:
        exists = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone()
        if exists:
            raise ValueError("用户名已存在")
        conn.execute(
            "INSERT INTO users (username, password_hash, role, name, department, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (username, hash_password(password), role, name, department, time.strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
    finally:
        conn.close()
    return {"username": username, "role": role, "name": name, "department": department}


def verify_login(username: str, password: str) -> dict | None:
    """校验登录，成功返回用户信息，失败返回 None。"""
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    finally:
        conn.close()
    if row is None or not row["active"] or not verify_password(password, row["password_hash"]):
        return None
    return {
        "username": row["username"],
        "role": row["role"],
        "name": row["name"],
        "department": row["department"] or "",
    }


def list_users() -> list:
    """返回所有用户（不含密码哈希）。"""
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT id, username, role, name, department, created_at, active FROM users ORDER BY id"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_user(username: str) -> dict | None:
    """按用户名返回用户（不含密码），用于令牌有效性与停用状态校验。"""
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT id, username, role, name, department, created_at, active FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_managed_user(username: str, password: str, name: str, role: str, department: str = "") -> dict:
    """管理员创建账号；与开放注册不同，可创建三类角色。"""
    if role not in {"admin", "staff", "user"}:
        raise ValueError("无效角色")
    if role == "staff" and department not in DEPARTMENTS:
        raise ValueError("部门人员必须选择有效的所属部门")
    if role != "staff":
        department = "信息中心" if role == "admin" else ""
    conn = get_conn()
    try:
        if conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
            raise ValueError("用户名已存在")
        cur = conn.execute(
            "INSERT INTO users (username, password_hash, role, name, department, created_at, active) "
            "VALUES (?, ?, ?, ?, ?, ?, 1)",
            (username, hash_password(password), role, name, department, time.strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        user_id = cur.lastrowid
    finally:
        conn.close()
    return {**get_user(username), "id": user_id}


def update_managed_user(user_id: int, *, name: str, role: str, department: str, active: bool) -> dict:
    """管理员更新用户资料和启停状态，用户名保持不变。"""
    if role not in {"admin", "staff", "user"}:
        raise ValueError("无效角色")
    if role == "staff" and department not in DEPARTMENTS:
        raise ValueError("部门人员必须选择有效的所属部门")
    if role != "staff":
        department = "信息中心" if role == "admin" else ""
    conn = get_conn()
    try:
        row = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            raise ValueError("用户不存在")
        if row["username"] == "admin" and (role != "admin" or not active):
            raise ValueError("预置超级管理员不能停用或降级")
        conn.execute(
            "UPDATE users SET name = ?, role = ?, department = ?, active = ? WHERE id = ?",
            (name, role, department, int(active), user_id),
        )
        conn.commit()
        username = row["username"]
    finally:
        conn.close()
    return get_user(username)


# ---------------------------------------------------------------------------
# 群众诉求（citizen_appeals）
# ---------------------------------------------------------------------------
def _init_citizen_appeals() -> None:
    """建群众诉求表（幂等，含满意度字段）。"""
    conn = get_conn()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS citizen_appeals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT NOT NULL,
                region TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT '已受理',
                satisfaction REAL,
                create_time TEXT NOT NULL
            )
            """
        )
        # 兼容旧表：若无 satisfaction 列则补齐
        cols = [r["name"] for r in conn.execute("PRAGMA table_info(citizen_appeals)").fetchall()]
        if "satisfaction" not in cols:
            conn.execute("ALTER TABLE citizen_appeals ADD COLUMN satisfaction REAL")
        conn.commit()
    finally:
        conn.close()


def submit_appeal(username: str, content: str, category: str, region: str) -> dict:
    """群众提交诉求，返回记录（含自增 id）。"""
    _init_citizen_appeals()
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO citizen_appeals (username, content, category, region, status, create_time) "
            "VALUES (?, ?, ?, ?, '已受理', ?)",
            (username, content, category, region, now),
        )
        conn.commit()
        appeal_id = cur.lastrowid
    finally:
        conn.close()
    return {
        "id": appeal_id,
        "username": username,
        "content": content,
        "category": category,
        "region": region,
        "status": "已受理",
        "create_time": now,
    }


def list_appeals_by_user(username: str) -> list:
    """返回某用户的诉求列表（倒序）。"""
    _init_citizen_appeals()
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT id, content, category, region, status, satisfaction, create_time "
            "FROM citizen_appeals WHERE username = ? ORDER BY id DESC",
            (username,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
