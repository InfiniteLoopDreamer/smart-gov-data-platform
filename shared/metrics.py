"""
KPI 指标计算模块。

本模块只做纯数据计算（不依赖 Streamlit），输入 DataFrame、输出结果字典，
便于单元测试与复用。所有时间比较均以“当日 0 点”为基准进行环比计算。
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from shared import forecast

# 政务大厅固定开放窗口数（用于计算窗口使用率）
TOTAL_WINDOWS = 120

# 在办（尚未办结）状态集合
OPEN_STATUSES = {"待受理", "办理中", "待审批"}


def _safe_mean(series: pd.Series, default: float = 0.0) -> float:
    """安全计算均值，空序列返回默认值。"""
    if series is None or len(series) == 0:
        return default
    return float(series.mean())


def _safe_count(series: pd.Series) -> int:
    """安全计数。"""
    return 0 if series is None else int(len(series))


def compute_kpis(cases: pd.DataFrame) -> dict:
    """计算首页 4 项核心 KPI（含环比变化）。

    Args:
        cases (pd.DataFrame): 办件工单表。

    Returns:
        dict: 包含 4 项 KPI 的数值、单位、环比增量与涨跌颜色语义。
    """
    today = pd.Timestamp.now().normalize()
    yesterday = today - pd.Timedelta(days=1)

    submit_day = cases["submit_time"].dt.normalize()
    today_mask = submit_day == today
    yesterday_mask = submit_day == yesterday

    # 1. 今日办件量（较昨日）
    today_count = _safe_count(cases[today_mask])
    yesterday_count = _safe_count(cases[yesterday_mask])
    count_delta = today_count - yesterday_count

    # 2. 平均办理时长（已办结件，近 7 日 vs 前 7 日，单位：小时）
    finished = cases[(cases["status"] == "已办结") & cases["duration_hours"].notna()]
    cutoff7 = today - pd.Timedelta(days=7)
    cutoff14 = today - pd.Timedelta(days=14)
    recent_dur = finished[finished["submit_time"] >= cutoff7]["duration_hours"]
    prev_dur = finished[
        (finished["submit_time"] >= cutoff14) & (finished["submit_time"] < cutoff7)
    ]["duration_hours"]
    avg_duration = _safe_mean(recent_dur, 0.0)
    avg_duration_prev = _safe_mean(prev_dur, avg_duration)
    duration_delta = avg_duration - avg_duration_prev

    # 3. 窗口使用率（今日在办工单数 / 总窗口数，较昨日，封顶 100%）
    open_today = _safe_count(
        cases[today_mask & cases["status"].isin(OPEN_STATUSES)]
    )
    open_yesterday = _safe_count(
        cases[yesterday_mask & cases["status"].isin(OPEN_STATUSES)]
    )
    usage = min(1.0, open_today / TOTAL_WINDOWS)
    usage_prev = min(1.0, open_yesterday / TOTAL_WINDOWS)
    usage_delta = usage - usage_prev

    # 4. 群众满意度（近 7 日已办结件满意度均值，5 分制，较前 7 日）
    sat_mask = (cases["status"] == "已办结") & cases["satisfaction"].notna()
    recent_sat = cases[sat_mask & (cases["submit_time"] >= cutoff7)]["satisfaction"]
    prev_sat = cases[
        sat_mask
        & (cases["submit_time"] >= cutoff14)
        & (cases["submit_time"] < cutoff7)
    ]["satisfaction"]
    avg_sat = _safe_mean(recent_sat, 0.0)
    avg_sat_prev = _safe_mean(prev_sat, avg_sat)
    sat_delta = avg_sat - avg_sat_prev

    return {
        "today_count": {
            "value": f"{today_count:,}",
            "delta": int(count_delta),
            "label": "较昨日",
            "delta_color": "normal",
        },
        "avg_duration": {
            "value": f"{avg_duration:.1f}小时",
            "delta": round(duration_delta, 1),
            "label": "较前7日",
            "delta_color": "inverse",
        },
        "window_usage": {
            "value": f"{usage * 100:.1f}%",
            "delta": round(usage_delta * 100, 1),
            "label": "较昨日",
            "delta_color": "normal",
        },
        "satisfaction": {
            "value": f"{avg_sat:.2f}分",
            "delta": round(sat_delta, 2),
            "label": "较前7日",
            "delta_color": "normal",
        },
    }


def compute_trend(cases: pd.DataFrame, days: int = 7) -> pd.DataFrame:
    """计算近 N 天每日办件量趋势。

    Args:
        cases (pd.DataFrame): 办件工单表。
        days (int): 统计最近多少天。

    Returns:
        pd.DataFrame: 含 date / count / finished_count 三列，按日期升序。
    """
    today = pd.Timestamp.now().normalize()
    start = today - pd.Timedelta(days=days - 1)
    recent = cases[cases["submit_time"] >= start]

    daily = (
        recent.groupby(recent["submit_time"].dt.normalize())
        .agg(count=("case_id", "count"), finished_count=("status", lambda s: (s == "已办结").sum()))
        .reset_index()
        .rename(columns={"submit_time": "date"})
    )
    # 显式转 int，避免 pandas 3.x 下 Arrow 字符串 dtype 导致 reindex 填充失败
    daily["count"] = pd.to_numeric(daily["count"], errors="coerce").fillna(0).astype(int)
    daily["finished_count"] = pd.to_numeric(daily["finished_count"], errors="coerce").fillna(0).astype(int)

    # 补齐缺失日期为 0，保证折线图连续
    full_dates = pd.date_range(start, today, freq="D")
    daily = daily.set_index("date").reindex(full_dates, fill_value=0).reset_index()
    daily = daily.rename(columns={"index": "date"})
    daily["date"] = pd.to_datetime(daily["date"])
    return daily


def compute_top_items(cases: pd.DataFrame, top: int = 5) -> pd.DataFrame:
    """统计高频办理事项 TOP N。

    Args:
        cases (pd.DataFrame): 办件工单表。
        top (int): 返回前几名。

    Returns:
        pd.DataFrame: 含 item_type / count 两列，按数量升序（便于水平条形图）。
    """
    top_df = (
        cases.groupby("item_type")
        .size()
        .rename("count")
        .reset_index()
        .sort_values("count", ascending=True)
        .tail(top)
    )
    return top_df


def compute_appeal_region_heat(regions: pd.DataFrame, appeals: pd.DataFrame) -> pd.DataFrame:
    """将诉求量按区域聚合，并关联区域坐标用于热力/气泡图。

    Args:
        regions (pd.DataFrame): 区域信息表。
        appeals (pd.DataFrame): 群众诉求表。

    Returns:
        pd.DataFrame: 区域 + 坐标 + 诉求量。
    """
    counts = appeals.groupby("region").size().rename("appeal_count").reset_index()
    merged = regions.merge(counts, left_on="region_name", right_on="region", how="left")
    merged["appeal_count"] = merged["appeal_count"].fillna(0).astype(int)
    return merged


def compute_appeal_category_stats(appeals: pd.DataFrame) -> pd.DataFrame:
    """统计诉求分类的数量与占比。

    Args:
        appeals (pd.DataFrame): 群众诉求表。

    Returns:
        pd.DataFrame: 含 category / count / ratio 三列，按数量降序。
    """
    stats = (
        appeals.groupby("category")
        .size()
        .rename("count")
        .reset_index()
        .sort_values("count", ascending=False)
    )
    stats["ratio"] = stats["count"] / stats["count"].sum()
    return stats


def compute_appeal_trend(appeals: pd.DataFrame, days: int = 14) -> pd.DataFrame:
    """计算近 N 天每日诉求量趋势。

    Args:
        appeals (pd.DataFrame): 群众诉求表。
        days (int): 统计最近多少天。

    Returns:
        pd.DataFrame: 含 date / count 两列。
    """
    today = pd.Timestamp.now().normalize()
    start = today - pd.Timedelta(days=days - 1)
    recent = appeals[appeals["create_time"] >= start]
    daily = (
        recent.groupby(recent["create_time"].dt.normalize())
        .size()
        .rename("count")
        .reset_index()
        .rename(columns={"create_time": "date"})
    )
    full_dates = pd.date_range(start, today, freq="D")
    daily = daily.set_index("date").reindex(full_dates, fill_value=0).reset_index()
    daily = daily.rename(columns={"index": "date"})
    daily["date"] = pd.to_datetime(daily["date"])
    return daily


def compute_department_ranking(cases: pd.DataFrame) -> pd.DataFrame:
    """计算部门效能排名（按已办结件平均办理时长 + 满意度加权）。

    Args:
        cases (pd.DataFrame): 办件工单表。

    Returns:
        pd.DataFrame: 含 department / case_count / avg_duration / avg_satisfaction / score 列。
    """
    finished = cases[cases["status"] == "已办结"]
    grp = finished.groupby("department").agg(
        case_count=("case_id", "count"),
        avg_duration=("duration_hours", "mean"),
        avg_satisfaction=("satisfaction", "mean"),
    ).reset_index()

    # 效能得分：满意度越高、时长越短，得分越高（归一化后加权）
    grp["score"] = (
        grp["avg_satisfaction"].fillna(0) * 40
        - grp["avg_duration"].fillna(0) * 2
    )
    grp["avg_duration"] = grp["avg_duration"].round(1)
    grp["avg_satisfaction"] = grp["avg_satisfaction"].round(2)
    grp = grp.sort_values("score", ascending=False).reset_index(drop=True)
    grp["rank"] = grp.index + 1
    return grp


def compute_pending_list(cases: pd.DataFrame, top: int = 8) -> pd.DataFrame:
    """生成待办中心列表（在办工单按紧急程度与时间排序）。

    Args:
        cases (pd.DataFrame): 办件工单表。
        top (int): 返回条数。

    Returns:
        pd.DataFrame: 含 case_id / title / urgency / status / submit_time 列。
    """
    pending = cases[cases["status"].isin(OPEN_STATUSES)].copy()
    urgency_order = {"紧急": 0, "高": 1, "中": 2, "低": 3}
    pending["_urgency_rank"] = pending["urgency"].map(urgency_order)
    pending = pending.sort_values(["_urgency_rank", "submit_time"], ascending=[True, False])
    cols = ["case_id", "title", "urgency", "status", "submit_time"]
    return pending[cols].head(top).reset_index(drop=True)


def compute_overdue_appeals(appeals: pd.DataFrame) -> pd.DataFrame:
    """筛选督办/超时工单（已督办或超时未办结）。

    Args:
        appeals (pd.DataFrame): 群众诉求表。

    Returns:
        pd.DataFrame: 督办流水（超时工单）列表。
    """
    overdue = appeals[
        (appeals["is_overdue"] == 1) | (appeals["status"] == "已督办")
    ].copy()
    cols = ["appeal_id", "content", "category", "region", "status", "create_time"]
    return overdue[cols].sort_values("create_time", ascending=False)


def compute_forecast(cases: pd.DataFrame, days_back: int = 21, days_forward: int = 7) -> dict:
    """基于 Holt-Winters 预测未来办件量（趋势 + 周季节 + 误差评估）。

    Args:
        cases (pd.DataFrame): 办件工单表。
        days_back (int): 用于拟合的历史天数。
        days_forward (int): 预测未来天数。

    Returns:
        dict: 历史日期、实际值、拟合值、预测值及 MAPE/RMSE 误差指标。
    """
    today = pd.Timestamp.now().normalize()
    start = today - pd.Timedelta(days=days_back - 1)
    recent = cases[cases["submit_time"] >= start]

    daily = (
        recent.groupby(recent["submit_time"].dt.normalize())
        .size()
        .rename("count")
        .reset_index()
        .rename(columns={"submit_time": "date"})
    )
    full_dates = pd.date_range(start, today, freq="D")
    daily = daily.set_index("date").reindex(full_dates, fill_value=0)
    daily.index.name = "date"

    values = daily["count"].values.astype(float)
    result = forecast.holt_winters(values, season_len=7, forecast_steps=days_forward)
    fitted = result["fitted"]
    predicted = np.clip(result["forecast"], 0, None)

    # 样本内一步预测的误差评估
    mask = ~np.isnan(fitted)
    mape_val = forecast.mape(values[mask], fitted[mask]) if mask.any() else None
    rmse_val = forecast.rmse(values[mask], fitted[mask]) if mask.any() else None

    moving_avg = daily["count"].rolling(window=7, min_periods=1).mean()

    return {
        "dates": list(daily.index),
        "actual": [int(v) for v in values],
        "moving_avg": [round(float(v), 1) for v in moving_avg.values],
        "fitted": [round(float(v), 1) if not np.isnan(v) else None for v in fitted],
        "future_dates": [d.date() for d in pd.date_range(today + pd.Timedelta(days=1), periods=days_forward)],
        "predicted": [int(round(v)) for v in predicted],
        "mape": round(mape_val, 2) if mape_val is not None else None,
        "rmse": round(rmse_val, 2) if rmse_val is not None else None,
        "method": "Holt-Winters（加法季节，周期 7 天）",
    }


def compute_anomalies(cases: pd.DataFrame, days_back: int = 60, threshold: float = 3.0) -> list:
    """检测办件量异常日期（基于 Holt-Winters 拟合残差的 3-sigma）。

    先用 Holt-Winters 去除趋势与周季节，再对残差做 z-score，
    避免把正常的高峰日误判为异常。

    Args:
        cases (pd.DataFrame): 办件工单表。
        days_back (int): 统计最近多少天。
        threshold (float): z-score 阈值（默认 3）。

    Returns:
        list: 异常点列表，含 date / count / z_score / direction。
    """
    today = pd.Timestamp.now().normalize()
    start = today - pd.Timedelta(days=days_back - 1)
    recent = cases[cases["submit_time"] >= start]

    daily = (
        recent.groupby(recent["submit_time"].dt.normalize())
        .size()
        .rename("count")
        .reset_index()
        .rename(columns={"submit_time": "date"})
    )
    full_dates = pd.date_range(start, today, freq="D")
    daily = daily.set_index("date").reindex(full_dates, fill_value=0)
    daily.index.name = "date"

    values = daily["count"].values.astype(float)
    anomalies = forecast.detect_anomalies(values, threshold=threshold, season_len=7)
    return [
        {
            "date": daily.index[a["index"]].strftime("%Y-%m-%d"),
            "count": int(a["value"]),
            "z_score": a["z_score"],
            "direction": "偏高" if a["z_score"] > 0 else "偏低",
        }
        for a in anomalies
    ]


def compute_data_quality(cases: pd.DataFrame, appeals: pd.DataFrame) -> dict:
    """从真实数据识别缺失 / 重复 / 异常 / 时间逻辑问题（数据质量监控）。

    Args:
        cases (pd.DataFrame): 办件工单表。
        appeals (pd.DataFrame): 群众诉求表。

    Returns:
        dict: 数据总量、完整率、问题清单与办件量异常点。
    """
    total_cases = _safe_count(cases)
    total_appeals = _safe_count(appeals)

    # 关键字段缺失 / 不规范（如区域未映射为 "Unspecified"）
    required = ["title", "department", "region", "item_type", "status", "urgency", "handler", "submit_time"]
    required = [c for c in required if c in cases.columns]
    bad_mask = pd.Series(False, index=cases.index) if total_cases else pd.Series(dtype=bool)
    if required:
        bad_mask = cases[required].isna().any(axis=1)
    if "region" in cases.columns:
        bad_mask = bad_mask | (cases["region"] == "Unspecified")
    region_unspecified = int(bad_mask.sum()) if total_cases else 0
    completeness = round((total_cases - region_unspecified) / total_cases * 100, 2) if total_cases else 100.0

    # 重复诉求：内容 + 分类 + 区域 + 提交时间完全一致
    dup_cols = [c for c in ("content", "category", "region", "create_time") if c in appeals.columns]
    duplicate_appeals = int(appeals.duplicated(dup_cols).sum()) if dup_cols and total_appeals else 0

    # 时间逻辑：办结时间早于受理时间
    time_violations = 0
    if {"submit_time", "finish_time"}.issubset(cases.columns):
        submit = pd.to_datetime(cases["submit_time"], errors="coerce")
        finish = pd.to_datetime(cases["finish_time"], errors="coerce")
        time_violations = int((finish < submit).sum())

    # 办件量异常日期（Holt-Winters 残差 3-sigma）
    anomalies = compute_anomalies(cases)

    issues = [
        {
            "field": "区域 region",
            "issue_type": "缺失",
            "count": region_unspecified,
            "detail": f"{region_unspecified} 条办件的区域未映射（Unspecified），需按区域字典补齐",
        },
        {
            "field": "诉求内容 content",
            "issue_type": "重复",
            "count": duplicate_appeals,
            "detail": f"{duplicate_appeals} 条诉求内容、分类、区域与提交时间完全重复，建议合并去重",
        },
        {
            "field": "办理时长 duration",
            "issue_type": "时间逻辑",
            "count": time_violations,
            "detail": f"{time_violations} 条办件的办结时间早于受理时间，需校正时间字段",
        },
        {
            "field": "办件量时序",
            "issue_type": "异常",
            "count": len(anomalies),
            "detail": f"近 60 天检测到 {len(anomalies)} 个办件量异常日期（3-sigma）",
        },
    ]

    return {
        "total_cases": total_cases,
        "total_appeals": total_appeals,
        "total": total_cases + total_appeals,
        "completeness": completeness,
        "region_unspecified": region_unspecified,
        "duplicate_appeals": duplicate_appeals,
        "time_violations": time_violations,
        "issues": issues,
        "anomalies": anomalies,
    }


def compute_core_findings(cases: pd.DataFrame, appeals: pd.DataFrame) -> list:
    """基于数据自动生成核心发现（洞察）卡片。

    Args:
        cases (pd.DataFrame): 办件工单表。
        appeals (pd.DataFrame): 群众诉求表。

    Returns:
        list: 每项为 dict，含 icon / title / detail。
    """
    findings = []

    kpis = compute_kpis(cases)
    delta = kpis["today_count"]["delta"]
    trend_word = "上升" if delta > 0 else ("下降" if delta < 0 else "持平")
    findings.append(
        {
            "title": "办件量趋势",
            "detail": f"今日办件量较昨日{trend_word} {abs(delta)} 件，整体业务量保持平稳。",
        }
    )

    top_items = compute_top_items(cases, top=1)
    if len(top_items) > 0:
        top_item = top_items.iloc[-1]
        total = len(cases)
        ratio = top_item["count"] / total * 100 if total else 0
        findings.append(
            {
                "title": "高频事项",
                "detail": f"「{top_item['item_type']}」为最高频事项，占全部办件的 {ratio:.1f}%。",
            }
        )

    cat_stats = compute_appeal_category_stats(appeals)
    if len(cat_stats) > 0:
        top_cat = cat_stats.iloc[0]
        findings.append(
            {
                "title": "诉求热点",
                "detail": f"群众诉求集中在「{top_cat['category']}」，占全部诉求的 {top_cat['ratio'] * 100:.1f}%。",
            }
        )

    dept_rank = compute_department_ranking(cases)
    if len(dept_rank) > 0:
        top_dept = dept_rank.iloc[0]
        findings.append(
            {
                "title": "部门效能",
                "detail": f"「{top_dept['department']}」综合效能排名第一，办结 {int(top_dept['case_count'])} 件。",
            }
        )

    return findings


def compute_audit_alerts(audit_logs: pd.DataFrame) -> pd.DataFrame:
    """筛选安全审计中的告警（WARN / ERROR 级别日志）。

    Args:
        audit_logs (pd.DataFrame): 操作审计日志表。

    Returns:
        pd.DataFrame: 告警日志列表（按时间倒序）。
    """
    alerts = audit_logs[audit_logs["level"].isin(["WARN", "ERROR"])].copy()
    cols = ["log_id", "user", "operation", "module", "level", "ip_address", "op_time"]
    return alerts[cols].sort_values("op_time", ascending=False)
