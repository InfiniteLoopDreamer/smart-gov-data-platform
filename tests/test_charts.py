"""src.charts 图表 option 构造测试（仅校验返回结构，不渲染）。"""

import pandas as pd

from src import charts


def test_trend_line_structure():
    df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=3),
            "count": [1, 2, 3],
            "finished_count": [0, 1, 2],
        }
    )
    opt = charts.trend_line(df)
    assert "series" in opt and len(opt["series"]) == 2


def test_top_items_bar_structure():
    df = pd.DataFrame({"item_type": ["A", "B", "C"], "count": [10, 20, 30]})
    opt = charts.top_items_bar(df)
    assert opt["series"][0]["type"] == "bar"


def test_region_heatmap_structure():
    df = pd.DataFrame(
        {"region_name": ["东", "西"], "map_x": [10, 20], "map_y": [30, 40], "appeal_count": [5, 15]}
    )
    opt = charts.region_heatmap(df)
    assert opt["series"][0]["type"] == "scatter"
    assert "visualMap" in opt


def test_forecast_line_structure():
    fc = {
        "dates": pd.date_range("2024-01-01", periods=3),
        "actual": [1, 2, 3],
        "moving_avg": [1.0, 2.0, 3.0],
        "future_dates": pd.date_range("2024-01-04", periods=2),
        "predicted": [4, 5],
    }
    opt = charts.forecast_line(fc)
    assert len(opt["series"]) == 3


def test_appeal_category_donut_structure():
    df = pd.DataFrame({"category": ["城市管理", "交通出行"], "count": [10, 20]})
    opt = charts.appeal_category_donut(df)
    assert opt["series"][0]["type"] == "pie"


def test_department_ranking_bar_structure():
    df = pd.DataFrame({"department": ["A", "B"], "score": [90.0, 80.0]})
    opt = charts.department_ranking_bar(df)
    assert opt["series"][0]["type"] == "bar"
