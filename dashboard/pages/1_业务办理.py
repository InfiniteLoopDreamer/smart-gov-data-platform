"""
页面：业务办理（一网通办）。

包含三个功能点：
    1. 办件管理 —— 列表查询（状态/时间筛选）、详情查看、导出
    2. 审批服务 —— 待审批列表、通过/驳回操作
    3. 一件事导办 —— 办事指南、材料清单
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
import pandas as pd

# 项目根目录加入 sys.path，以便导入 shared 包
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared import metrics, state  # noqa: E402
from src import sidebar, utils  # noqa: E402
from src.data_loader import load_cases  # noqa: E402

# 一件事导办场景库（办事指南 + 材料清单）
ONE_THING_GUIDES = {
    "开办企业（一件事）": {
        "departments": "市场监管局、税务局、人社局",
        "days": "3 个工作日",
        "steps": [
            "网上提交企业名称预先核准申请",
            "在线填报企业设立登记信息并上传材料",
            "市场监管部门受理并审核（0.5 个工作日）",
            "领取营业执照（可邮寄或电子证照）",
            "同步完成税务登记、社保开户（数据共享，免重复填报）",
        ],
        "materials": [
            ("企业设立登记申请书", "申请人自备", "原件电子件"),
            ("法定代表人身份证明", "公安部门", "原件扫描件"),
            ("公司章程", "申请人自备", "原件电子件"),
            ("住所（经营场所）使用证明", "住建/物业", "复印件"),
        ],
    },
    "新生儿出生（一件事）": {
        "departments": "卫健委、公安局、医保局",
        "days": "1 个工作日",
        "steps": [
            "医院端一次填报新生儿出生信息",
            "卫健委核发出生医学证明（电子证照）",
            "公安部门在线办理出生登记（落户）",
            "医保部门自动参保登记并制卡",
        ],
        "materials": [
            ("出生医学证明申请表", "医院", "原件电子件"),
            ("父母双方身份证", "公安部门", "原件扫描件"),
            ("结婚证", "民政部门", "原件扫描件"),
            ("户口簿", "公安部门", "原件扫描件"),
        ],
    },
    "二手房过户（一件事）": {
        "departments": "自然资源局、税务局、住建局",
        "days": "2 个工作日",
        "steps": [
            "网上预约过户并核验房屋权属",
            "在线提交买卖双方身份与合同材料",
            "税务部门核定税费并在线缴纳",
            "不动产登记部门受理、审核、登簿",
            "领取不动产权证书（可邮寄）",
        ],
        "materials": [
            ("不动产权证书", "自然资源局", "原件扫描件"),
            ("房屋买卖合同", "买卖双方自备", "原件电子件"),
            ("买卖双方身份证明", "公安部门", "原件扫描件"),
            ("完税证明", "税务部门", "电子件"),
        ],
    },
}


def render_case_management(cases: pd.DataFrame) -> None:
    """功能点：办件管理（列表查询 + 详情查看 + 导出）。"""
    utils.render_section_title("办件管理", "列表查询、详情查看与数据导出")

    # 筛选器
    f1, f2, f3 = st.columns([1, 1, 2])
    with f1:
        status_options = ["全部"] + sorted(cases["status"].unique().tolist())
        status_filter = st.selectbox("办理状态", status_options)
    with f2:
        dept_options = ["全部"] + sorted(cases["department"].unique().tolist())
        dept_filter = st.selectbox("办理部门", dept_options)
    with f3:
        min_date = cases["submit_time"].min().date()
        max_date = cases["submit_time"].max().date()
        date_range = st.date_input("提交时间范围", value=(min_date, max_date), min_value=min_date, max_value=max_date)

    # 应用筛选
    filtered = cases.copy()
    if status_filter != "全部":
        filtered = filtered[filtered["status"] == status_filter]
    if dept_filter != "全部":
        filtered = filtered[filtered["department"] == dept_filter]
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = date_range
        filtered = filtered[
            (filtered["submit_time"].dt.date >= start) & (filtered["submit_time"].dt.date <= end)
        ]

    st.caption(f"共筛选出 {len(filtered):,} 条办件记录")

    # 导出按钮
    st.download_button(
        label="导出筛选结果（CSV）",
        data=filtered.to_csv(index=False).encode("utf-8-sig"),
        file_name="办件数据.csv",
        mime="text/csv",
    )

    # 列表展示
    show_cols = ["case_id", "title", "department", "region", "item_type", "status", "urgency", "submit_time"]
    st.dataframe(
        filtered[show_cols].rename(
            columns={
                "case_id": "工单编号",
                "title": "标题",
                "department": "办理部门",
                "region": "所属区域",
                "item_type": "事项类型",
                "status": "状态",
                "urgency": "紧急程度",
                "submit_time": "提交时间",
            }
        ),
        hide_index=True,
        use_container_width=True,
        height=380,
    )

    # 详情查看
    st.markdown("---")
    st.markdown("#### 办件详情查看")
    if not filtered.empty:
        case_id = st.selectbox("选择工单编号", filtered["case_id"].tolist())
        detail = filtered[filtered["case_id"] == case_id].iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("办理部门", detail["department"])
        c2.metric("事项类型", detail["item_type"])
        c3.metric("办理状态", detail["status"])
        c4.metric("紧急程度", detail["urgency"])
        c5, c6, c7, c8 = st.columns(4)
        c5.metric("办理人", detail["handler"])
        c6.metric("提交时间", detail["submit_time"].strftime("%m-%d %H:%M"))
        c7.metric("办理时长", f"{detail['duration_hours']}小时" if pd.notna(detail["duration_hours"]) else "办理中")
        c8.metric("满意度", f"{detail['satisfaction']}分" if pd.notna(detail["satisfaction"]) else "-")
        st.info(f"办件标题：{detail['title']}　|　所属区域：{detail['region']}")
    else:
        st.info("当前筛选条件下无办件记录")


def render_approval_service(cases: pd.DataFrame) -> None:
    """功能点：审批服务（待审批列表 + 通过/驳回操作）。"""
    utils.render_section_title("审批服务", "对待审批工单进行通过 / 驳回操作")

    # 从持久化状态读取已审批记录（刷新页面不丢失）
    approved_ids, rejected_ids = state.get_approval_ids()

    pending = cases[cases["status"] == "待审批"].copy()
    processed = approved_ids | rejected_ids
    pending = pending[~pending["case_id"].isin(processed)]

    c1, c2 = st.columns([3, 1])
    with c1:
        st.caption(f"当前待审批工单：{len(pending)} 件")
    with c2:
        if st.button("重置审批状态", use_container_width=True):
            state.reset_approval()
            st.rerun()

    if pending.empty:
        st.success("当前没有待审批工单，全部处理完毕！")
        return

    for _, row in pending.head(10).iterrows():
        c1, c2, c3, c4, c5 = st.columns([1.5, 3, 1.2, 1.0, 1.0])
        c1.markdown(f"`{row['case_id']}`")
        c2.markdown(row["title"])
        c3.markdown(f"<span style='color:{utils.COLOR_MUTED};font-size:0.82rem;'>{row['item_type']}</span>", unsafe_allow_html=True)
        if c4.button("通过", key=f"approve_{row['case_id']}", use_container_width=True):
            state.set_approval("approved", row["case_id"])
            st.toast(f"已审批通过：{row['case_id']}")
            st.rerun()
        if c5.button("驳回", key=f"reject_{row['case_id']}", use_container_width=True):
            state.set_approval("rejected", row["case_id"])
            st.toast(f"已驳回：{row['case_id']}")
            st.rerun()

    st.markdown("---")
    st.markdown("**批量审批区**")
    selected = st.multiselect("选择工单进行批量操作", pending["case_id"].head(20).tolist())
    b1, b2 = st.columns(2)
    if b1.button("批量通过", use_container_width=True, disabled=not selected):
        state.set_approval("approved", selected)
        st.toast(f"已批量通过 {len(selected)} 件")
        st.rerun()
    if b2.button("批量驳回", use_container_width=True, disabled=not selected):
        state.set_approval("rejected", selected)
        st.toast(f"已批量驳回 {len(selected)} 件")
        st.rerun()


def render_one_thing_guide() -> None:
    """功能点：一件事导办（办事指南 + 材料清单）。"""
    utils.render_section_title("一件事导办", "主题式集成服务，一次申报、多部门联办")

    scenario = st.selectbox("选择「一件事」场景", list(ONE_THING_GUIDES.keys()))
    guide = ONE_THING_GUIDES[scenario]

    c1, c2 = st.columns(2)
    c1.metric("涉及部门", guide["departments"])
    c2.metric("承诺办结时限", guide["days"])

    left, right = st.columns([1, 1])
    with left:
        st.markdown("#### 办事指南（办理流程）")
        for i, step in enumerate(guide["steps"], start=1):
            st.markdown(
                utils.clean_html(
                    f"""
                    <div style="display:flex;gap:10px;align-items:flex-start;margin-bottom:10px;">
                        <div style="min-width:24px;height:24px;border-radius:50%;background:{utils.COLOR_CYAN};
                                    color:{utils.COLOR_BG};font-weight:800;display:flex;align-items:center;
                                    justify-content:center;font-size:0.8rem;">{i}</div>
                        <div style="font-size:0.88rem;color:{utils.COLOR_TEXT};line-height:1.6;">{step}</div>
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )
    with right:
        st.markdown("#### 材料清单")
        material_df = pd.DataFrame(guide["materials"], columns=["材料名称", "材料来源", "材料形式"])
        st.dataframe(material_df, hide_index=True, use_container_width=True)


def main() -> None:
    """业务办理页面主流程。"""
    sidebar.setup_page("智慧政务大数据平台 · 业务办理")
    utils.render_section_title("业务办理 · 一网通办", "让群众办事少跑腿、数据多跑路")

    try:
        cases = load_cases()
    except FileNotFoundError as exc:
        st.error("数据文件缺失，请先运行 `python generate_data.py` 生成数据。")
        st.info(str(exc))
        return

    tab1, tab2, tab3 = st.tabs(["办件管理", "审批服务", "一件事导办"])
    with tab1:
        render_case_management(cases)
    with tab2:
        render_approval_service(cases)
    with tab3:
        render_one_thing_guide()


if __name__ == "__main__":
    main()
