"""shared/forecast 时间序列预测与异常检测测试。"""

import numpy as np
import pandas as pd

from shared import forecast, metrics


def test_holt_winters_captures_seasonality():
    # 生成带周季节 + 上升趋势的平滑数据
    t = np.arange(42)  # 6 周
    values = 100 + 0.5 * t + 30 * np.sin(2 * np.pi * t / 7)
    result = forecast.holt_winters(values, season_len=7, forecast_steps=7)
    assert len(result["forecast"]) == 7
    assert (result["forecast"] > 0).all()
    # 样本内拟合误差应较小
    fitted = result["fitted"][7:]
    actual = values[7:]
    assert forecast.mape(actual, fitted) < 20


def test_mape_rmse_mae():
    import pytest
    actual = np.array([100.0, 200.0, 300.0])
    predicted = np.array([110.0, 190.0, 330.0])
    assert forecast.mape(actual, predicted) is not None
    assert forecast.rmse(actual, predicted) > 0
    assert forecast.mae(actual, predicted) == pytest.approx(50 / 3, abs=0.01)


def test_detect_anomalies_finds_outlier():
    t = np.arange(35)
    values = 100 + 10 * np.sin(2 * np.pi * t / 7)  # 平滑季节
    values[20] += 80  # 制造一个明显异常
    anomalies = forecast.detect_anomalies(values, threshold=3.0, season_len=7)
    assert any(a["index"] == 20 for a in anomalies)


def test_detect_anomalies_no_outlier_on_smooth_data():
    t = np.arange(35)
    values = 100 + 10 * np.sin(2 * np.pi * t / 7)  # 无异常
    anomalies = forecast.detect_anomalies(values, threshold=3.0, season_len=7)
    assert anomalies == []


def _make_cases(n_days=40, per_day=20) -> pd.DataFrame:
    """构造带周季节 + 趋势的办件表。"""
    rows = []
    today = pd.Timestamp.now().normalize()
    for d in range(n_days):
        day = today - pd.Timedelta(days=d)
        count = int(per_day + 8 * np.sin(2 * np.pi * d / 7) + (n_days - d) * 0.3)
        for i in range(count):
            rows.append({"case_id": f"C{len(rows):04d}", "submit_time": day})
    return pd.DataFrame(rows)


def test_compute_forecast_has_metrics():
    result = metrics.compute_forecast(_make_cases(), days_back=21, days_forward=7)
    assert "mape" in result and "rmse" in result and "fitted" in result
    assert len(result["predicted"]) == 7
    assert len(result["fitted"]) == 21
    assert result["method"].startswith("Holt-Winters")


def test_compute_anomalies_structure():
    anomalies = metrics.compute_anomalies(_make_cases(), days_back=40, threshold=3.0)
    assert isinstance(anomalies, list)
    for a in anomalies:
        assert {"date", "count", "z_score", "direction"}.issubset(a.keys())
