"""
时间序列预测与异常检测模块。

纯 numpy 实现，无第三方依赖：
    - Holt-Winters 加法季节性指数平滑（趋势 + 周期项），用于办件量预测
    - 误差指标：MAPE / RMSE / MAE
    - 3-sigma 异常检测（基于拟合残差的 z-score）
"""

from __future__ import annotations

import numpy as np


def holt_winters(
    values,
    season_len: int = 7,
    forecast_steps: int = 7,
    alpha: float = 0.3,
    beta: float = 0.1,
    gamma: float = 0.1,
) -> dict:
    """Holt-Winters 加法季节性指数平滑（趋势 + 周期项）。

    Args:
        values: 等间隔时序数据（如每日办件量）。
        season_len: 季节周期（默认 7 = 周）。
        forecast_steps: 未来预测步数。
        alpha/beta/gamma: 水平 / 趋势 / 季节平滑系数。

    Returns:
        dict: {"fitted": 样本内一步预测（前 season_len 个为 NaN），
               "forecast": 未来 forecast_steps 步预测}
    """
    values = np.asarray(values, dtype=float)
    n = len(values)
    if n == 0:
        return {"fitted": np.array([]), "forecast": np.zeros(forecast_steps)}
    if season_len < 1:
        season_len = 1
    if n < season_len:
        season_len = max(1, n)

    # 初始化：水平用首个周期均值，趋势用前后两周期均值差，季节为相对水平的偏差
    level = float(np.mean(values[:season_len]))
    if n >= 2 * season_len:
        trend = (float(np.mean(values[season_len:2 * season_len])) - float(np.mean(values[:season_len]))) / season_len
    else:
        trend = 0.0
    season = np.array([values[i] - level for i in range(season_len)], dtype=float)

    fitted = np.full(n, np.nan)
    for t in range(n):
        forecast = level + trend + season[t % season_len]
        if t >= season_len:
            fitted[t] = forecast
        actual = values[t]
        prev_level = level
        level = alpha * (actual - season[t % season_len]) + (1 - alpha) * (prev_level + trend)
        trend = beta * (level - prev_level) + (1 - beta) * trend
        season[t % season_len] = gamma * (actual - level) + (1 - gamma) * season[t % season_len]

    # 未来预测
    forecast = []
    l, tr = level, trend
    for h in range(1, forecast_steps + 1):
        forecast.append(float(l + h * tr + season[(n + h - 1) % season_len]))

    return {"fitted": fitted, "forecast": np.array(forecast)}


def mape(actual, predicted) -> float | None:
    """平均绝对百分比误差（MAPE，%）。actual 为 0 的样本跳过。"""
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    mask = actual != 0
    if not mask.any():
        return None
    return float(np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100)


def rmse(actual, predicted) -> float:
    """均方根误差。"""
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    return float(np.sqrt(np.mean((actual - predicted) ** 2)))


def mae(actual, predicted) -> float:
    """平均绝对误差。"""
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    return float(np.mean(np.abs(actual - predicted)))


def detect_anomalies(values, threshold: float = 3.0, season_len: int = 7) -> list:
    """基于拟合残差 z-score 的异常检测。

    先用 Holt-Winters 拟合去除趋势与季节，再对残差计算 z-score，
    |z| > threshold 的样本判为异常（避免把正常的高峰日误判为异常）。

    Args:
        values: 时序数据。
        threshold: z-score 阈值（默认 3，即 3-sigma）。
        season_len: 季节周期。

    Returns:
        list: 异常点列表，每项含 index / value / z_score。
    """
    values = np.asarray(values, dtype=float)
    n = len(values)
    if n <= season_len:
        return []

    result = holt_winters(values, season_len=season_len)
    fitted = result["fitted"]
    idx = np.arange(season_len, n)
    residuals = values[season_len:] - fitted[season_len:]
    std = float(residuals.std())
    if std == 0:
        return []
    z = residuals / std
    anomalies = []
    for pos, zi in enumerate(z):
        if abs(zi) > threshold:
            anomalies.append(
                {"index": int(idx[pos]), "value": float(values[idx[pos]]), "z_score": float(round(zi, 2))}
            )
    return anomalies
