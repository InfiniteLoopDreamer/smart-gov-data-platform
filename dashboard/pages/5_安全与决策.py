"""
页面：安全与决策。

包含三个功能点：
    1. 安全审计 —— 操作日志展示、告警
    2. 领导看板 —— 精简看板
    3. 趋势预测 —— 移动平均预测
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# 项目根目录加入 sys.path，以便导入 shared 包
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared import metrics  # noqa: E402
from src import charts, sidebar, utils  # noqa: E402
from src.data_loader import load_audit_logs, load_cases, load_appeals  # noqa: E402


def render_security_audit(audit_logs) -> None:
    """功能点：安全审计（操作日志展示 + 告警）。"""
    utils.render_section_title("安全审计", "操作日志展示与安全告警")

    alerts = metrics.compute_audit_alerts(audit_logs)

    # 告警汇总
    c1, c2, c3 = st.columns(3)
    c1.metric("日志总量", f"{len(audit_logs):,}")
    c2.metric("告警日志", len(alerts), help="WARN / ERROR 级别日志")
    c3.metric("告警占比", f"{len(alerts) / max(len(audit_logs), 1) * 100:.1f}%")

    st.markdown("#### 安全告警（WARN / ERROR）")
    if alerts.empty:
        st.success("暂无安全告警")
    else:
        for _, row in alerts.head(8).iterrows():
            color = "#F87171" if row["level"] == "ERROR" else "#FBBF24"
            st.markdown(
                utils.clean_html(
                    f"""
                    <div style="background:{utils.COLOR_CARD};border-left:4px solid {color};
                                border-radius:8px;padding:10px 14px;margin-bottom:8px;">
                        <div style="display:flex;align-items:center;gap:8px;">
                            <span style="color:{color};font-weight:800;font-size:0.8rem;">[{row['level']}]</span>
                            <span style="color:{utils.COLOR_TEXT};font-weight:600;">{row['operation']}</span>
                            <span style="margin-left:auto;font-size:0.78rem;color:{utils.COLOR_MUTED};">
                                {row['op_time']:%m-%d %H:%M} · {row['ip_address']}
                            </span>
                        </div>
                        <div style="font-size:0.78rem;color:{utils.COLOR_MUTED};margin-top:4px;">
                            用户：{row['user']} · 模块：{row['module']} · 编号：{row['log_id']}
                        </div>
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )

    # 日志筛选展示
    st.markdown("#### 操作日志")
    level_filter = st.selectbox("日志级别", ["全部", "INFO", "WARN", "ERROR"])
    logs = audit_logs if level_filter == "全部" else audit_logs[audit_logs["level"] == level_filter]
    st.dataframe(
        logs.head(300).rename(
            columns={
                "log_id": "日志编号",
                "user": "操作用户",
                "module": "功能模块",
                "operation": "操作内容",
                "level": "级别",
                "ip_address": "来源IP",
                "op_time": "操作时间",
            }
        ),
        hide_index=True,
        use_container_width=True,
        height=340,
    )


def render_leader_dashboard(cases, appeals) -> None:
    """功能点：领导看板（精简看板）。"""
    utils.render_section_title("领导看板", "面向决策者的精简运行态势")

    kpis = metrics.compute_kpis(cases)
    top_items = metrics.compute_top_items(cases, top=5)
    cat_stats = metrics.compute_appeal_category_stats(appeals)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("今日办件量", kpis["today_count"]["value"], delta=kpis["today_count"]["delta"])
    c2.metric("平均办理时长", kpis["avg_duration"]["value"], delta=kpis["avg_duration"]["delta"])
    c3.metric("窗口使用率", kpis["window_usage"]["value"], delta=kpis["window_usage"]["delta"])
    c4.metric("群众满意度", kpis["satisfaction"]["value"], delta=kpis["satisfaction"]["delta"])

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    left, right = st.columns([3, 2])
    with left:
        trend_df = metrics.compute_trend(cases, days=7)
        charts.render_chart(charts.trend_line(trend_df), height=300)
    with right:
        charts.render_chart(charts.top_items_bar(top_items), height=300)

    # 关键结论
    findings = metrics.compute_core_findings(cases, appeals)
    st.markdown("#### 关键结论")
    for item in findings[:3]:
        st.markdown(
            f"<div style='font-size:0.9rem;color:{utils.COLOR_TEXT};padding:6px 0;'>"
            f"<b>{item['title']}</b>：{item['detail']}</div>",
            unsafe_allow_html=True,
        )


def render_forecast(cases) -> None:
    """功能点：趋势预测（Holt-Winters 季节预测 + 误差评估 + 异常检测）。"""
    utils.render_section_title("趋势预测", "Holt-Winters 季节预测 · 误差评估 · 异常检测")

    forecast = metrics.compute_forecast(cases, days_back=28, days_forward=7)
    charts.render_chart(charts.forecast_line(forecast), height=360)

    # 误差评估
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("MAPE 平均百分比误差", f"{forecast['mape']:.2f}%" if forecast.get("mape") is not None else "-")
    c2.metric("RMSE 均方根误差", f"{forecast['rmse']:.2f}" if forecast.get("rmse") is not None else "-")
    c3.metric("未来 7 日预测均值", f"{sum(forecast['predicted']) // 7:,}")
    growth = (sum(forecast["predicted"]) - sum(forecast["actual"][-7:])) / max(sum(forecast["actual"][-7:]), 1) * 100
    c4.metric("预测增长率", f"{growth:+.1f}%")

    st.caption("说明：使用 Holt-Winters 加法季节指数平滑（趋势 + 周季节，周期 7 天）对近 28 天办件量建模，并给出 MAPE/RMSE 误差评估。")

    # 异常检测
    st.markdown("#### 办件量异常检测（3-sigma）")
    anomalies = metrics.compute_anomalies(cases, days_back=60, threshold=3.0)
    if not anomalies:
        st.success("近 60 天未检测到显著异常日期。")
    else:
        df = pd.DataFrame(anomalies).rename(
            columns={"date": "日期", "count": "办件量", "z_score": "Z 分数", "direction": "方向"}
        )
        st.dataframe(df, hide_index=True, use_container_width=True)
        st.caption("基于 Holt-Winters 拟合残差的 3-sigma 检测：去除趋势与周季节后识别显著异常波动。")


def main() -> None:
    """安全与决策页面主流程。"""
    sidebar.setup_page("智慧政务大数据平台 · 安全与决策")
    utils.render_section_title("安全与决策", "安全审计保障 + 数据驱动决策")

    try:
        audit_logs = load_audit_logs()
        cases = load_cases()
        appeals = load_appeals()
    except FileNotFoundError as exc:
        st.error("数据文件缺失，请先运行 `python generate_data.py` 生成数据。")
        st.info(str(exc))
        return

    tab1, tab2, tab3 = st.tabs(["安全审计", "领导看板", "趋势预测"])
    with tab1:
        render_security_audit(audit_logs)
    with tab2:
        render_leader_dashboard(cases, appeals)
    with tab3:
        render_forecast(cases)


if __name__ == "__main__":
    main()
