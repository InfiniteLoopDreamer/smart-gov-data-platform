"""
页面：监督调度。

包含三个功能点：
    1. 社情民意 —— 诉求分类统计、趋势
    2. 督办流水 —— 超时工单列表
    3. 考核评价 —— 部门效能排名
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# 项目根目录加入 sys.path，以便导入 shared 包
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared import metrics  # noqa: E402
from src import charts, sidebar, utils  # noqa: E402
from src.data_loader import load_appeals, load_cases  # noqa: E402


def render_public_opinion(appeals) -> None:
    """功能点：社情民意（诉求分类统计 + 趋势）。"""
    utils.render_section_title("社情民意", "群众诉求分类统计与趋势分析")

    cat_stats = metrics.compute_appeal_category_stats(appeals)
    trend_df = metrics.compute_appeal_trend(appeals, days=14)

    left, right = st.columns([2, 3])
    with left:
        charts.render_chart(charts.appeal_category_donut(cat_stats), height=300)
    with right:
        charts.render_chart(charts.appeal_trend_line(trend_df), height=300)

    st.markdown("#### 诉求分类明细")
    st.dataframe(
        cat_stats.assign(占比=lambda d: (d["ratio"] * 100).round(1).astype(str) + "%").rename(
            columns={"category": "诉求分类", "count": "诉求量", "ratio": "原始占比", "占比": "占比"}
        )[["诉求分类", "诉求量", "占比"]],
        hide_index=True,
        use_container_width=True,
    )


def render_supervision(appeals) -> None:
    """功能点：督办流水（超时工单列表）。"""
    utils.render_section_title("督办流水", "超时未办结工单督办跟踪")

    overdue = metrics.compute_overdue_appeals(appeals)

    c1, c2 = st.columns(2)
    c1.metric("超时工单总数", len(overdue))
    c2.metric("已督办", int((overdue["status"] == "已督办").sum()))

    if overdue.empty:
        st.success("暂无超时工单")
        return

    st.dataframe(
        overdue.rename(
            columns={
                "appeal_id": "诉求编号",
                "content": "诉求内容",
                "category": "分类",
                "region": "区域",
                "status": "状态",
                "create_time": "创建时间",
            }
        ),
        hide_index=True,
        use_container_width=True,
        height=380,
    )

    st.caption("督办建议：超时工单应优先分流至对应部门，并自动升级预警。")


def render_assessment(cases) -> None:
    """功能点：考核评价（部门效能排名）。"""
    utils.render_section_title("考核评价", "部门办件效能综合排名")

    rank_df = metrics.compute_department_ranking(cases)

    charts.render_chart(charts.department_ranking_bar(rank_df), height=360)

    st.markdown("#### 部门效能明细")
    st.dataframe(
        rank_df.rename(
            columns={
                "rank": "排名",
                "department": "部门",
                "case_count": "办结件数",
                "avg_duration": "平均时长(小时)",
                "avg_satisfaction": "平均满意度",
                "score": "综合得分",
            }
        )[["排名", "部门", "办结件数", "平均时长(小时)", "平均满意度", "综合得分"]],
        hide_index=True,
        use_container_width=True,
    )


def main() -> None:
    """监督调度页面主流程。"""
    sidebar.setup_page("智慧政务大数据平台 · 监督调度")
    utils.render_section_title("监督调度", "社情民意监测、督办跟踪与效能考核")

    try:
        appeals = load_appeals()
        cases = load_cases()
    except FileNotFoundError as exc:
        st.error("数据文件缺失，请先运行 `python generate_data.py` 生成数据。")
        st.info(str(exc))
        return

    tab1, tab2, tab3 = st.tabs(["社情民意", "督办流水", "考核评价"])
    with tab1:
        render_public_opinion(appeals)
    with tab2:
        render_supervision(appeals)
    with tab3:
        render_assessment(cases)


if __name__ == "__main__":
    main()
