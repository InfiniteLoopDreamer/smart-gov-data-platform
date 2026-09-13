"""
数据加载与缓存模块。

负责从 data/ 目录读取 6 张 CSV 数据表，并通过 Streamlit 缓存机制
（@st.cache_data）避免重复磁盘 IO 与解析，提升页面响应速度。

若数据文件缺失，会抛出带中文提示的异常，引导用户先运行数据生成脚本。
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# 路径与表名映射
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

DATA_FILES = {
    "departments": "departments.csv",
    "regions": "regions.csv",
    "cases": "cases.csv",
    "appeals": "appeals.csv",
    "inspections": "inspections.csv",
    "audit_logs": "audit_logs.csv",
}

# 各表需要解析为 datetime 的列
DATETIME_COLS = {
    "cases": ["submit_time", "finish_time"],
    "appeals": ["create_time", "resolve_time"],
    "inspections": ["plan_time", "finish_time"],
    "audit_logs": ["op_time"],
}


# ---------------------------------------------------------------------------
# 底层读取
# ---------------------------------------------------------------------------
def _read_csv(name: str) -> pd.DataFrame:
    """读取单个 CSV 文件并完成基础类型转换。

    Args:
        name (str): 表名（见 DATA_FILES 的键）。

    Returns:
        pd.DataFrame: 解析后的数据表。

    Raises:
        FileNotFoundError: 数据文件缺失时抛出，提示先运行生成脚本。
    """
    path = DATA_DIR / DATA_FILES[name]
    if not path.exists():
        raise FileNotFoundError(
            f"数据文件缺失：{path.name}\n"
            f"请先在项目根目录运行 `python generate_data.py` 生成模拟数据。"
        )

    df = pd.read_csv(path)

    # 将时间列统一解析为 datetime（空字符串转换为 NaT）
    for col in DATETIME_COLS.get(name, []):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # 办件表中的满意度等数值列统一转为 float，空值保留为 NaN
    for col in ("duration_hours", "satisfaction"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


# ---------------------------------------------------------------------------
# 对外接口（带缓存）
# ---------------------------------------------------------------------------
@st.cache_data(ttl=300, show_spinner=False)
def load_departments() -> pd.DataFrame:
    """加载部门信息表。"""
    return _read_csv("departments")


@st.cache_data(ttl=300, show_spinner=False)
def load_regions() -> pd.DataFrame:
    """加载区域信息表。"""
    return _read_csv("regions")


@st.cache_data(ttl=300, show_spinner=False)
def load_cases() -> pd.DataFrame:
    """加载办件工单表。"""
    return _read_csv("cases")


@st.cache_data(ttl=300, show_spinner=False)
def load_appeals() -> pd.DataFrame:
    """加载群众诉求表。"""
    return _read_csv("appeals")


@st.cache_data(ttl=300, show_spinner=False)
def load_inspections() -> pd.DataFrame:
    """加载综合巡查任务表。"""
    return _read_csv("inspections")


@st.cache_data(ttl=300, show_spinner=False)
def load_audit_logs() -> pd.DataFrame:
    """加载操作审计日志表。"""
    return _read_csv("audit_logs")


@st.cache_data(ttl=300, show_spinner=False)
def load_all() -> dict:
    """一次性加载全部 6 张数据表。

    Returns:
        dict: 以表名为键、DataFrame 为值的字典。
    """
    return {
        "departments": load_departments(),
        "regions": load_regions(),
        "cases": load_cases(),
        "appeals": load_appeals(),
        "inspections": load_inspections(),
        "audit_logs": load_audit_logs(),
    }
