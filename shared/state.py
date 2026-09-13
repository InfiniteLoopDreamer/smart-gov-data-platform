"""
本地持久化状态模块。

审批「通过/驳回」等需要跨会话保留的操作状态，持久化到 data/app_state.json，
刷新页面或重启应用后仍保留，体现「状态持久化」而非仅内存态。
"""

from __future__ import annotations

import json
from pathlib import Path

STATE_FILE = Path(__file__).resolve().parent.parent / "data" / "app_state.json"


def load_state() -> dict:
    """读取持久化状态。

    Returns:
        dict: 状态字典；文件不存在或损坏时返回空字典。
    """
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_state(state: dict) -> None:
    """写入持久化状态（覆盖写）。"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def get_approval_ids() -> tuple:
    """读取已审批的办件编号集合。

    Returns:
        tuple: (已通过集合, 已驳回集合)。
    """
    state = load_state()
    return set(state.get("approved_ids", [])), set(state.get("rejected_ids", []))


def set_approval(kind: str, ids) -> None:
    """记录审批结果（累加）。

    Args:
        kind (str): 'approved' 或 'rejected'。
        ids: 单个编号或编号的可迭代对象。
    """
    if isinstance(ids, str):
        ids = [ids]
    state = load_state()
    key = f"{kind}_ids"
    merged = set(state.get(key, [])) | set(ids)
    state[key] = sorted(merged)
    save_state(state)


def reset_approval() -> None:
    """清空审批记录。"""
    state = load_state()
    state.pop("approved_ids", None)
    state.pop("rejected_ids", None)
    save_state(state)
