"""src.data_loader 数据加载测试（依赖 data/*.csv）。"""

import pytest

from src.data_loader import _read_csv, DATA_DIR

pytestmark = pytest.mark.skipif(
    not (DATA_DIR / "cases.csv").exists(),
    reason="data/*.csv 不存在，请先运行 python generate_data.py",
)


def test_read_cases_has_columns():
    df = _read_csv("cases")
    assert {"case_id", "title", "department", "region", "status", "submit_time"}.issubset(df.columns)
    assert len(df) > 0


def test_read_regions_has_required_columns():
    df = _read_csv("regions")
    assert len(df) > 0
    assert {"region_name", "map_x", "map_y"}.issubset(df.columns)


def test_read_appeals_parses_datetime():
    df = _read_csv("appeals")
    assert str(df["create_time"].dtype).startswith("datetime")
