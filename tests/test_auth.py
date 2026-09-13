"""src.auth 认证模块测试（密码哈希 / 令牌 / 用户管理，隔离到临时 DB）。"""

import pytest

from shared import auth


def test_hash_and_verify_password():
    hashed = auth.hash_password("secret123")
    assert auth.verify_password("secret123", hashed)
    assert not auth.verify_password("wrong", hashed)


def test_token_roundtrip():
    token = auth.create_token({"username": "admin", "role": "admin"})
    payload = auth.decode_token(token)
    assert payload["username"] == "admin"
    assert payload["role"] == "admin"


def test_token_tamper_rejected():
    token = auth.create_token({"username": "admin", "role": "admin"})
    body, sig = token.split(".")
    bad = f"{body}.{'0' * len(sig)}"
    with pytest.raises(ValueError):
        auth.decode_token(bad)


def test_init_db_and_login(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, "DB_PATH", tmp_path / "auth.db")
    auth.init_db()
    assert auth.verify_login("admin", "admin123") is not None
    assert auth.verify_login("admin", "wrong") is None
    assert auth.verify_login("user", "user123")["role"] == "user"


def test_register_and_duplicate(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, "DB_PATH", tmp_path / "auth.db")
    auth.init_db()
    auth.register_user("newuser", "pass123", "新用户")
    assert auth.verify_login("newuser", "pass123") is not None
    with pytest.raises(ValueError):
        auth.register_user("newuser", "pass123", "重复注册")
