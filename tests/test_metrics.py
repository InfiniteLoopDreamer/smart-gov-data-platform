"""src.metrics 纯函数单元测试。

所有测试使用构造的小型 DataFrame，不依赖 generate_data.py 生成的数据，
保证测试快速、确定、可离线运行。
"""

import pandas as pd

from shared import metrics

TODAY = pd.Timestamp.now().normalize()


def _make_cases(n=40) -> pd.DataFrame:
    """构造含时间、状态、时长、满意度的办件表。"""
    departments = ["市公安局", "市市场监管局", "市人社局"]
    items = ["企业开办", "社保参保", "公积金提取"]
    statuses = ["已办结", "办理中", "待审批", "待受理", "已驳回"]
    urg = ["紧急", "高", "中", "低"]
    rows = []
    for i in range(n):
        day_offset = i % 10
        submit = TODAY - pd.Timedelta(days=day_offset)
        status = statuses[i % len(statuses)]
        finished = status in ("已办结", "已驳回")
        rows.append(
            {
                "case_id": f"BJ{i:04d}",
                "title": f"事项{i}",
                "department": departments[i % 3],
                "region": "城东区",
                "item_type": items[i % 3],
                "status": status,
                "urgency": urg[i % 4],
                "handler": "张伟",
                "submit_time": submit,
                "finish_time": submit + pd.Timedelta(hours=2) if finished else pd.NaT,
                "duration_hours": float((i % 20) + 1) if finished else None,
                "satisfaction": round(3 + (i % 20) / 10, 1) if finished else None,
            }
        )
    return pd.DataFrame(rows)


def _make_appeals(n=20) -> pd.DataFrame:
    """构造诉求表。"""
    rows = []
    for i in range(n):
        day_offset = i % 7
        rows.append(
            {
                "appeal_id": f"SQ{i:04d}",
                "content": f"诉求内容{i}",
                "category": ["城市管理", "交通出行", "民生保障"][i % 3],
                "region": "城东区",
                "status": "已办结" if i % 2 == 0 else "已督办",
                "is_overdue": 1 if i % 2 == 1 else 0,
                "create_time": TODAY - pd.Timedelta(days=day_offset),
                "resolve_time": TODAY - pd.Timedelta(days=day_offset - 1),
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 测试
# ---------------------------------------------------------------------------
def test_compute_kpis_has_required_keys():
    kpis = metrics.compute_kpis(_make_cases())
    for key in ("today_count", "avg_duration", "window_usage", "satisfaction"):
        assert key in kpis
        assert "value" in kpis[key] and "delta" in kpis[key]


def test_compute_trend_returns_requested_days():
    trend = metrics.compute_trend(_make_cases(), days=7)
    assert len(trend) == 7
    assert {"date", "count", "finished_count"}.issubset(trend.columns)


def test_compute_top_items_sorted_ascending():
    cases = pd.DataFrame({"item_type": ["A"] * 5 + ["B"] * 3 + ["C"] * 2})
    top = metrics.compute_top_items(cases, top=2)
    # 数量升序，最高频在最后一行
    assert list(top["item_type"]) == ["B", "A"]
    assert top["count"].tolist() == [3, 5]


def test_compute_pending_list_excludes_finished():
    pending = metrics.compute_pending_list(_make_cases(), top=50)
    assert pending["status"].isin({"待受理", "办理中", "待审批"}).all()


def test_compute_department_ranking_sorted_by_score():
    rank = metrics.compute_department_ranking(_make_cases())
    scores = rank["score"].tolist()
    assert scores == sorted(scores, reverse=True)
    assert "rank" in rank.columns


def test_compute_forecast_shape():
    forecast = metrics.compute_forecast(_make_cases(), days_back=21, days_forward=7)
    assert len(forecast["actual"]) == 21
    assert len(forecast["moving_avg"]) == 21
    assert len(forecast["predicted"]) == 7


def test_compute_appeal_category_stats_ratio_sums_to_one():
    stats = metrics.compute_appeal_category_stats(_make_appeals())
    assert abs(stats["ratio"].sum() - 1.0) < 1e-9


def test_compute_overdue_appeals_filters():
    overdue = metrics.compute_overdue_appeals(_make_appeals())
    assert "appeal_id" in overdue.columns
    # n=20，奇数下标 10 条为超时/已督办
    assert len(overdue) == 10
    assert (overdue["status"] == "已督办").all()
