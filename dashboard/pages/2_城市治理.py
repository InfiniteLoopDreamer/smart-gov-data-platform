"""
页面：城市治理（一网统管）。

包含三个功能点：
    1. 城市一张图 —— 区域示意地图 + 巡查事件点位
    2. 综合巡查 —— 巡查任务列表 + 记录填报
    3. 联动指挥 —— 协同工单展示
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from src import charts, sidebar, utils
from src.data_loader import load_regions, load_inspections

INSPECTION_TYPE_LIST = ["市容市貌", "安全生产", "食品安全", "消防安全", "环境污染", "交通秩序"]


def render_city_map(regions: pd.DataFrame, inspections: pd.DataFrame) -> None:
    """功能点：城市一张图（地图 + 事件点位）。"""
    utils.render_section_title("城市一张图", "区域态势总览与事件点位分布")

    # 将巡查事件关联到区域坐标，用于地图渲染
    events = inspections.merge(
        regions[["region_name", "map_x", "map_y"]],
        left_on="region",
        right_on="region_name",
        how="left",
    ).dropna(subset=["map_x", "map_y"])
    # 仅取近期事件，避免点位过于密集
    events = events.sort_values("plan_time", ascending=False).head(150)

    charts.render_chart(charts.city_map(regions, events), height=380)

    # 图例说明
    c1, c2, c3 = st.columns(3)
    c1.metric("巡查事件点位", len(events))
    c2.metric("发现问题", int((events["result"] == "发现问题").sum()))
    c3.metric("覆盖区域", events["region"].nunique())


def render_inspection_list(inspections: pd.DataFrame) -> None:
    """功能点：综合巡查（任务列表 + 记录填报）。"""
    utils.render_section_title("综合巡查", "巡查任务列表与现场记录填报")

    # 筛选
    f1, f2 = st.columns(2)
    with f1:
        status_filter = st.selectbox("巡查状态", ["全部"] + sorted(inspections["status"].unique().tolist()))
    with f2:
        type_filter = st.selectbox("巡查类型", ["全部"] + INSPECTION_TYPE_LIST)

    filtered = inspections.copy()
    if status_filter != "全部":
        filtered = filtered[filtered["status"] == status_filter]
    if type_filter != "全部":
        filtered = filtered[filtered["inspection_type"] == type_filter]

    st.dataframe(
        filtered.rename(
            columns={
                "inspection_id": "任务编号",
                "region": "区域",
                "inspection_type": "巡查类型",
                "status": "状态",
                "inspector": "巡查员",
                "plan_time": "计划时间",
                "finish_time": "完成时间",
                "result": "结果",
                "remark": "备注",
            }
        ),
        hide_index=True,
        use_container_width=True,
        height=320,
    )


def render_inspection_form(regions: pd.DataFrame) -> None:
    """功能点：综合巡查（记录填报表单）。"""
    st.markdown("#### 巡查记录填报")

    if "inspection_records" not in st.session_state:
        st.session_state["inspection_records"] = []

    with st.form("inspection_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            region = st.selectbox("巡查区域", regions["region_name"].tolist())
            itype = st.selectbox("巡查类型", INSPECTION_TYPE_LIST)
        with c2:
            result = st.selectbox("巡查结果", ["正常", "发现问题"])
            inspector = st.text_input("巡查员姓名", value="")
        remark = st.text_area("情况描述", placeholder="请描述现场巡查情况…")
        submitted = st.form_submit_button("提交巡查记录", use_container_width=True)

    if submitted:
        record = {
            "区域": region,
            "巡查类型": itype,
            "巡查结果": result,
            "巡查员": inspector or "未填写",
            "情况描述": remark or "无",
            "填报时间": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        st.session_state["inspection_records"].append(record)
        st.toast("巡查记录已提交")

    if st.session_state["inspection_records"]:
        st.markdown("**已提交记录**")
        st.dataframe(
            pd.DataFrame(st.session_state["inspection_records"]),
            hide_index=True,
            use_container_width=True,
        )


def render_joint_command(inspections: pd.DataFrame) -> None:
    """功能点：联动指挥（协同工单展示）。"""
    utils.render_section_title("联动指挥", "跨部门协同工单与联动处置")

    # 协同工单：巡查发现问题的记录
    joint = inspections[inspections["result"] == "发现问题"].copy()
    if joint.empty:
        st.info("当前暂无需要联动的协同工单")
        return

    # 模拟联动处置状态
    status_cycle = (["待联动", "已联动", "处置中"] * (len(joint) // 3 + 1))[: len(joint)]
    joint["联动状态"] = status_cycle

    st.caption(f"共 {len(joint)} 件协同工单需要跨部门联动处置")
    show_cols = ["inspection_id", "region", "inspection_type", "联动状态", "remark", "plan_time"]
    st.dataframe(
        joint[show_cols].rename(
            columns={
                "inspection_id": "工单编号",
                "region": "区域",
                "inspection_type": "事件类型",
                "联动状态": "联动状态",
                "remark": "事件描述",
                "plan_time": "上报时间",
            }
        ),
        hide_index=True,
        use_container_width=True,
        height=320,
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("待联动", int((joint["联动状态"] == "待联动").sum()))
    c2.metric("已联动", int((joint["联动状态"] == "已联动").sum()))
    c3.metric("处置中", int((joint["联动状态"] == "处置中").sum()))


def main() -> None:
    """城市治理页面主流程。"""
    sidebar.setup_page("智慧政务大数据平台 · 城市治理")
    utils.render_section_title("城市治理 · 一网统管", "全域感知、快速响应、协同处置")

    try:
        regions = load_regions()
        inspections = load_inspections()
    except FileNotFoundError as exc:
        st.error("数据文件缺失，请先运行 `python generate_data.py` 生成数据。")
        st.info(str(exc))
        return

    tab1, tab2, tab3 = st.tabs(["城市一张图", "综合巡查", "联动指挥"])
    with tab1:
        render_city_map(regions, inspections)
    with tab2:
        render_inspection_list(inspections)
        st.markdown("---")
        render_inspection_form(regions)
    with tab3:
        render_joint_command(inspections)


if __name__ == "__main__":
    main()
