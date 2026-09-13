"""src.state 本地持久化模块测试（隔离到临时文件）。"""

from shared import state


def test_approval_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "app_state.json")
    state.set_approval("approved", ["A1", "A2"])
    state.set_approval("rejected", ["B1"])
    approved, rejected = state.get_approval_ids()
    assert approved == {"A1", "A2"}
    assert rejected == {"B1"}


def test_approval_accepts_single_string(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "app_state.json")
    state.set_approval("approved", "X")
    approved, _ = state.get_approval_ids()
    assert approved == {"X"}


def test_reset_approval(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "app_state.json")
    state.set_approval("approved", "X")
    state.set_approval("rejected", "Y")
    state.reset_approval()
    approved, rejected = state.get_approval_ids()
    assert approved == set() and rejected == set()


def test_load_state_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "not_exist.json")
    assert state.load_state() == {}
