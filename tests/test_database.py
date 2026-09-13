"""src.database SQLite 访问模块测试（依赖 data/gov_data.db）。"""

import pytest

from shared import database

pytestmark = pytest.mark.skipif(
    not database.DB_PATH.exists(),
    reason="gov_data.db 不存在，请先运行 python generate_data.py",
)


def test_list_tables():
    tables = set(database.list_tables())
    assert {"departments", "regions", "cases", "appeals", "inspections", "audit_logs"}.issubset(tables)


def test_read_table_returns_dataframe():
    df = database.read_table("departments")
    assert len(df) > 0
    assert "department_name" in df.columns


def test_case_status_stats():
    df = database.case_status_stats()
    assert {"状态", "数量"}.issubset(df.columns)
    assert len(df) >= 1


def test_case_by_region():
    df = database.case_by_region()
    assert {"区域", "办件量"}.issubset(df.columns)
    assert len(df) > 0
