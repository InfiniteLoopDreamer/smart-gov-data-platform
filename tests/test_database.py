"""shared.database SQLite 访问模块测试（依赖 data/gov_data.db）。"""

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


def test_core_data_integrity():
    cases = database.query(
        """SELECT COUNT(*) AS total,
                  COUNT(DISTINCT case_id) AS unique_ids,
                  SUM(CASE WHEN submit_time IS NULL THEN 1 ELSE 0 END) AS missing_dates,
                  SUM(CASE WHEN item_type IS NULL OR TRIM(item_type) = '' THEN 1 ELSE 0 END) AS missing_types
           FROM cases"""
    ).iloc[0]
    appeals = database.query(
        "SELECT COUNT(*) AS total, COUNT(DISTINCT appeal_id) AS unique_ids FROM appeals"
    ).iloc[0]
    assert cases["total"] == 50_000
    assert cases["unique_ids"] == cases["total"]
    assert cases["missing_dates"] == 0
    assert cases["missing_types"] == 0
    assert appeals["total"] == cases["total"]
    assert appeals["unique_ids"] == appeals["total"]
