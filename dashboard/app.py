"""
智慧政务大数据平台 - 主入口（首页：一屏统览）。

运行方式：
    streamlit run app.py

首页内容：
    - 顶部标题栏（含实时时钟）
    - 4 项核心 KPI 指标卡（直角包边 + 彩色标识点 + 环比箭头）
    - 全市政务办件趋势折线图（近 7 天）
    - 全市诉求热力分布图
    - 高频事项 TOP5 水平条形图
    - 待办中心列表（含处理按钮）
    - 核心发现卡片（数字徽标）
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# 项目根目录加入 sys.path，以便导入 shared 包
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared import metrics  # noqa: E402
from src import charts, sidebar, utils  # noqa: E402
from src.data_loader import load_all  # noqa: E402


# 紧急程度对应的徽标配色
URGENCY_BADGE = {
    "紧急": "#F87171",
    "高": "#FB923C",
    "中": "#FBBF24",
    "低": "#22D3EE",
}


def render_pending_center(cases) -> None:
    """渲染待办中心列表（工单编号、标题、紧急程度、时间、处理按钮）。"""
    st.markdown(
        f'<div style="font-size:1.05rem;font-weight:700;color:{utils.COLOR_TEXT};'
        f'margin-bottom:10px;padding-left:10px;border-left:3px solid {utils.COLOR_GOLD};">待办中心</div>',
        unsafe_allow_html=True,
    )
    pending = metrics.compute_pending_list(cases)

    if pending.empty:
        st.info("暂无待办工单")
        return

    # 表头
    header = st.columns([1.5, 3.2, 1.0, 1.6, 0.9])
    for col, text in zip(header, ["工单编号", "标题", "紧急程度", "提交时间", "操作"]):
        col.markdown(
            f'<div style="font-size:0.75rem;color:{utils.COLOR_MUTED};font-weight:600;">{text}</div>',
            unsafe_allow_html=True,
        )

    for _, row in pending.iterrows():
        cols = st.columns([1.5, 3.2, 1.0, 1.6, 0.9])
        badge_color = URGENCY_BADGE.get(row["urgency"], utils.COLOR_CYAN)
        cols[0].markdown(f"`{row['case_id']}`")
        cols[1].markdown(row["title"])
        cols[2].markdown(
            f'<span style="background:{badge_color}22;color:{badge_color};border:1px solid {badge_color}66;'
            f'padding:2px 8px;border-radius:10px;font-size:0.72rem;">{row["urgency"]}</span>',
            unsafe_allow_html=True,
        )
        cols[3].markdown(
            f'<span style="font-size:0.8rem;color:{utils.COLOR_MUTED};">{row["submit_time"]:%m-%d %H:%M}</span>',
            unsafe_allow_html=True,
        )
        if cols[4].button("处理", key=f"pending_{row['case_id']}", use_container_width=True):
            st.toast(f"已进入处理流程：{row['case_id']} · {row['title']}")


def render_core_findings(findings: list) -> None:
    """渲染核心发现卡片（自动生成的数据洞察，数字徽标）。"""
    st.markdown(
        f'<div style="font-size:1.05rem;font-weight:700;color:{utils.COLOR_TEXT};'
        f'margin:18px 0 10px 0;padding-left:10px;border-left:3px solid {utils.COLOR_CYAN};">核心发现</div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(len(findings))
    accents = [utils.COLOR_CYAN, utils.COLOR_GOLD, "#4F8CFF", "#34D399"]
    for i, (col, item, accent) in enumerate(zip(cols, findings, accents)):
        col.markdown(
            utils.clean_html(
                f"""
                <div style="position:relative;background:linear-gradient(150deg,rgba(15,32,56,0.85),rgba(8,20,38,0.6));
                            border:1px solid rgba(34,211,238,0.2);border-radius:10px;padding:14px 16px;height:150px;
                            box-shadow:0 4px 16px rgba(0,0,0,0.35);">
                    <span style="position:absolute;top:-1px;left:-1px;width:10px;height:10px;border-top:2px solid {accent};border-left:2px solid {accent};"></span>
                    <span style="position:absolute;bottom:-1px;right:-1px;width:10px;height:10px;border-bottom:2px solid {accent};border-right:2px solid {accent};"></span>
                    <div style="display:flex;align-items:center;gap:8px;">
                        <span style="font-size:1.15rem;font-weight:800;color:{accent};opacity:0.9;">{i + 1:02d}</span>
                        <span style="font-size:0.95rem;font-weight:700;color:{accent};">{item['title']}</span>
                    </div>
                    <div style="font-size:0.8rem;color:{utils.COLOR_MUTED};line-height:1.55;margin-top:8px;">{item['detail']}</div>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )


def main() -> None:
    """首页主流程。"""
    # 统一初始化：页面配置 + CSS + 侧边栏 + 顶部标题栏
    sidebar.setup_page("智慧政务大数据平台 · 一屏统览")

    # 加载数据（缺失时给出友好提示，不崩溃）
    try:
        data = load_all()
    except FileNotFoundError as exc:
        st.error("数据文件缺失，无法展示平台内容。")
        st.markdown("请先在项目根目录执行以下命令生成模拟数据：")
        st.code("python generate_data.py", language="bash")
        st.info(str(exc))
        return

    cases = data["cases"]
    appeals = data["appeals"]
    regions = data["regions"]

    # 1. 核心 KPI 指标卡
    kpis = metrics.compute_kpis(cases)
    utils.render_kpi_cards(kpis)

    # 2. 办件趋势折线图 + 高频事项 TOP5
    left, right = st.columns([3, 2])
    with left:
        trend_df = metrics.compute_trend(cases, days=7)
        charts.render_chart(charts.trend_line(trend_df), height=300)
    with right:
        top_df = metrics.compute_top_items(cases, top=5)
        charts.render_chart(charts.top_items_bar(top_df), height=300)

    # 3. 诉求热力图 + 待办中心
    left, right = st.columns([2, 3])
    with left:
        region_heat_df = metrics.compute_appeal_region_heat(regions, appeals)
        charts.render_chart(charts.region_heatmap(region_heat_df), height=320)
    with right:
        render_pending_center(cases)

    # 4. 核心发现卡片
    findings = metrics.compute_core_findings(cases, appeals)
    render_core_findings(findings)


if __name__ == "__main__":
    main()
