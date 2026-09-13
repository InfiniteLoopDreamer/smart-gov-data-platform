"""
页面：数据资源（一网共享）。

包含三个功能点：
    1. 数据资产 —— 数据表清单、字段说明、数据预览
    2. 资源目录 —— 分类浏览
    3. 数据服务 —— API 文档展示
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from src import sidebar, utils
from src.data_loader import load_all

# 数据表元信息（表名 -> 中文名 / 说明 / 资源分类）
TABLE_INFO = {
    "departments": {"name": "部门信息表", "desc": "政务部门基础信息，用于关联办件与部门效能排名", "category": "基础库"},
    "regions": {"name": "区域信息表", "desc": "行政区划、人口面积与示意地图坐标", "category": "地理库"},
    "cases": {"name": "办件工单表", "desc": "「一网通办」核心业务工单流水", "category": "业务库"},
    "appeals": {"name": "群众诉求表", "desc": "12345 群众诉求与社情民意数据", "category": "业务库"},
    "inspections": {"name": "综合巡查任务表", "desc": "「一网统管」巡查任务与事件记录", "category": "业务库"},
    "audit_logs": {"name": "操作审计日志表", "desc": "系统操作行为的安全审计日志", "category": "审计库"},
}

# 字段说明字典（表名 -> 字段名 -> 中文说明）
FIELD_DESC = {
    "departments": {
        "department_code": "部门编码",
        "department_name": "部门名称",
        "department_type": "部门类型",
        "responsibility": "主要职责",
        "employee_count": "在编人数",
    },
    "regions": {
        "region_code": "区域编码",
        "region_name": "区域名称",
        "population_wan": "常住人口（万）",
        "area_km2": "辖区面积（km²）",
        "map_x": "示意地图 X 坐标",
        "map_y": "示意地图 Y 坐标",
    },
    "cases": {
        "case_id": "工单编号",
        "title": "办件标题",
        "department": "办理部门",
        "region": "所属区域",
        "item_type": "事项类型",
        "status": "办理状态",
        "urgency": "紧急程度",
        "handler": "办理人",
        "submit_time": "提交时间",
        "finish_time": "办结时间",
        "duration_hours": "办理时长（小时）",
        "satisfaction": "群众满意度（分）",
    },
    "appeals": {
        "appeal_id": "诉求编号",
        "content": "诉求内容",
        "category": "诉求分类",
        "region": "所属区域",
        "status": "处理状态",
        "is_overdue": "是否超时（1 是 / 0 否）",
        "create_time": "创建时间",
        "resolve_time": "解决时间",
    },
    "inspections": {
        "inspection_id": "任务编号",
        "region": "所属区域",
        "inspection_type": "巡查类型",
        "status": "巡查状态",
        "inspector": "巡查员",
        "plan_time": "计划时间",
        "finish_time": "完成时间",
        "result": "巡查结果",
        "remark": "备注",
    },
    "audit_logs": {
        "log_id": "日志编号",
        "user": "操作用户",
        "module": "功能模块",
        "operation": "操作内容",
        "level": "日志级别",
        "ip_address": "来源 IP",
        "op_time": "操作时间",
    },
}

# 资源目录分类（分类 -> 资源列表）
RESOURCE_CATALOG = {
    "基础库": ["部门信息表", "区域信息表", "统一编码库"],
    "地理库": ["行政区划图层", "网格化地图", "POI 兴趣点"],
    "业务库": ["办件工单表", "群众诉求表", "综合巡查任务表"],
    "主题库": ["营商环境主题库", "民生保障主题库", "城市治理主题库"],
    "审计库": ["操作审计日志表", "数据访问留痕"],
}

# API 服务文档（模拟）
API_DOCS = [
    {"method": "GET", "path": "/api/v1/cases", "name": "办件列表查询", "params": "status, region, start_time, end_time", "desc": "分页查询办件工单，支持状态/区域/时间过滤"},
    {"method": "GET", "path": "/api/v1/cases/{id}", "name": "办件详情查询", "params": "id", "desc": "根据工单编号查询单条办件详情"},
    {"method": "POST", "path": "/api/v1/cases/approve", "name": "办件审批", "params": "case_id, action(pass/reject)", "desc": "对待审批工单执行通过或驳回操作"},
    {"method": "GET", "path": "/api/v1/appeals", "name": "诉求列表查询", "params": "category, region, status", "desc": "查询群众诉求，支持分类/区域/状态过滤"},
    {"method": "GET", "path": "/api/v1/stats/kpi", "name": "核心指标查询", "params": "date", "desc": "获取一屏统览首页核心 KPI 指标"},
    {"method": "GET", "path": "/api/v1/data/assets", "name": "数据资产目录", "params": "category", "desc": "获取数据资产清单与字段说明"},
]


def render_data_assets(data: dict) -> None:
    """功能点：数据资产（表清单 + 字段说明 + 预览）。"""
    utils.render_section_title("数据资产", "数据表清单、字段说明与数据预览")

    # 数据表清单
    summary_rows = []
    for key, info in TABLE_INFO.items():
        df = data[key]
        summary_rows.append(
            {
                "表名": key,
                "中文名称": info["name"],
                "资源分类": info["category"],
                "行数": len(df),
                "字段数": len(df.columns),
                "说明": info["desc"],
            }
        )
    summary_df = pd.DataFrame(summary_rows)
    st.dataframe(summary_df, hide_index=True, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 字段说明与数据预览")

    table_key = st.selectbox(
        "选择数据表",
        list(TABLE_INFO.keys()),
        format_func=lambda k: f"{k}（{TABLE_INFO[k]['name']}）",
    )
    df = data[table_key]

    # 字段说明
    field_rows = []
    for col in df.columns:
        field_rows.append(
            {
                "字段名": col,
                "字段说明": FIELD_DESC.get(table_key, {}).get(col, "-"),
                "数据类型": str(df[col].dtype),
                "示例值": str(df[col].iloc[0]) if len(df) else "-",
            }
        )
    st.markdown("**字段说明**")
    st.dataframe(pd.DataFrame(field_rows), hide_index=True, use_container_width=True)

    st.markdown("**数据预览（前 10 行）**")
    st.dataframe(df.head(10), hide_index=True, use_container_width=True)


def render_resource_catalog() -> None:
    """功能点：资源目录（分类浏览）。"""
    utils.render_section_title("资源目录", "按主题分类浏览共享数据资源")

    for category, items in RESOURCE_CATALOG.items():
        with st.expander(f"{category}（{len(items)} 项）", expanded=False):
            for item in items:
                st.markdown(
                    utils.clean_html(
                        f"""
                        <div style="display:flex;align-items:center;gap:8px;padding:6px 8px;
                                    border-bottom:1px dashed #1e3a5f;">
                            <span style="color:{utils.COLOR_CYAN};">▸</span>
                            <span style="color:{utils.COLOR_TEXT};font-size:0.9rem;">{item}</span>
                            <span style="margin-left:auto;font-size:0.72rem;color:{utils.COLOR_GOLD};
                                         border:1px solid {utils.COLOR_GOLD}55;border-radius:8px;padding:1px 8px;">
                                可共享
                            </span>
                        </div>
                        """
                    ),
                    unsafe_allow_html=True,
                )


def render_api_docs() -> None:
    """功能点：数据服务（API 文档展示）。"""
    utils.render_section_title("数据服务", "统一数据服务 API 接口文档")

    for api in API_DOCS:
        method_color = {"GET": utils.COLOR_CYAN, "POST": utils.COLOR_GOLD}.get(api["method"], utils.COLOR_CYAN)
        st.markdown(
            utils.clean_html(
                f"""
                <div style="background:{utils.COLOR_CARD};border:1px solid #1e3a5f;border-radius:12px;
                            padding:14px 18px;margin-bottom:10px;">
                    <div style="display:flex;align-items:center;gap:10px;">
                        <span style="background:{method_color};color:{utils.COLOR_BG};font-weight:800;
                                     font-size:0.72rem;padding:2px 10px;border-radius:6px;">{api['method']}</span>
                        <code style="color:{utils.COLOR_TEXT};font-size:0.9rem;">{api['path']}</code>
                        <span style="margin-left:auto;font-weight:700;color:{utils.COLOR_TEXT};">{api['name']}</span>
                    </div>
                    <div style="font-size:0.82rem;color:{utils.COLOR_MUTED};margin-top:8px;">{api['desc']}</div>
                    <div style="font-size:0.78rem;color:{utils.COLOR_CYAN};margin-top:6px;">参数：{api['params']}</div>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )
    st.caption("注：以上为演示用接口文档，返回格式均为 JSON，鉴权方式：Bearer Token。")


def main() -> None:
    """数据资源页面主流程。"""
    sidebar.setup_page("智慧政务大数据平台 · 数据资源")
    utils.render_section_title("数据资源 · 一网共享", "数据资产统一汇聚、统一目录、统一服务")

    try:
        data = load_all()
    except FileNotFoundError as exc:
        st.error("数据文件缺失，请先运行 `python generate_data.py` 生成数据。")
        st.info(str(exc))
        return

    tab1, tab2, tab3 = st.tabs(["数据资产", "资源目录", "数据服务"])
    with tab1:
        render_data_assets(data)
    with tab2:
        render_resource_catalog()
    with tab3:
        render_api_docs()


if __name__ == "__main__":
    main()
