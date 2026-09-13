"""
页面：系统管理。

功能点：
    1. 系统设置 —— 用户管理 + 系统配置
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from src import sidebar, utils

# 默认用户列表（演示用）
DEFAULT_USERS = [
    {"用户名": "admin", "姓名": "系统管理员", "角色": "超级管理员", "部门": "信息中心", "状态": "启用"},
    {"用户名": "zhangwei", "姓名": "张伟", "角色": "业务办理员", "部门": "市场监管局", "状态": "启用"},
    {"用户名": "lina", "姓名": "李娜", "角色": "审批员", "部门": "人社局", "状态": "启用"},
    {"用户名": "wangqiang", "姓名": "王强", "角色": "巡查员", "部门": "城市管理局", "状态": "启用"},
    {"用户名": "liuyang", "姓名": "刘洋", "角色": "数据分析师", "部门": "大数据中心", "状态": "停用"},
]

ROLES = ["超级管理员", "业务办理员", "审批员", "巡查员", "数据分析师", "访客"]


def render_user_management() -> None:
    """功能点：系统设置（用户管理）。"""
    utils.render_section_title("用户管理", "平台用户账号与权限管理")

    if "users" not in st.session_state:
        st.session_state["users"] = DEFAULT_USERS.copy()

    users = pd.DataFrame(st.session_state["users"])
    st.dataframe(users, hide_index=True, use_container_width=True)

    # 新增用户
    with st.expander("新增用户", expanded=False):
        with st.form("add_user_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                username = st.text_input("用户名", placeholder="英文登录名")
                name = st.text_input("姓名")
            with c2:
                role = st.selectbox("角色", ROLES)
                dept = st.text_input("所属部门")
            with c3:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                enabled = st.checkbox("启用账号", value=True)
            submitted = st.form_submit_button("保存用户", use_container_width=True)

        if submitted:
            if not username or not name:
                st.warning("请填写用户名与姓名")
            elif username in users["用户名"].tolist():
                st.warning("用户名已存在")
            else:
                st.session_state["users"].append(
                    {
                        "用户名": username,
                        "姓名": name,
                        "角色": role,
                        "部门": dept or "-",
                        "状态": "启用" if enabled else "停用",
                    }
                )
                st.toast(f"已新增用户：{username}")
                st.rerun()

    # 启用/停用
    st.markdown("#### 账号状态管理")
    user_list = users["用户名"].tolist()
    selected_user = st.selectbox("选择用户", user_list)
    target = users[users["用户名"] == selected_user].iloc[0]
    c1, c2 = st.columns(2)
    if c1.button("启用账号", use_container_width=True, disabled=target["状态"] == "启用"):
        for u in st.session_state["users"]:
            if u["用户名"] == selected_user:
                u["状态"] = "启用"
        st.rerun()
    if c2.button("停用账号", use_container_width=True, disabled=target["状态"] == "停用"):
        for u in st.session_state["users"]:
            if u["用户名"] == selected_user:
                u["状态"] = "停用"
        st.rerun()


def render_system_config() -> None:
    """功能点：系统设置（系统配置）。"""
    utils.render_section_title("系统配置", "平台运行参数配置")

    if "sys_config" not in st.session_state:
        st.session_state["sys_config"] = {
            "平台名称": "智慧政务大数据平台",
            "数据刷新周期(秒)": 60,
            "告警阈值(%)": 10,
            "主题风格": "深色政务科技风",
            "邮件通知": True,
            "短信通知": False,
        }

    cfg = st.session_state["sys_config"]

    with st.form("sys_config_form"):
        c1, c2 = st.columns(2)
        with c1:
            platform_name = st.text_input("平台名称", value=cfg["平台名称"])
            refresh = st.slider("数据刷新周期（秒）", 10, 300, cfg["数据刷新周期(秒)"], step=10)
            alert_threshold = st.slider("告警阈值（%）", 1, 50, cfg["告警阈值(%)"])
        with c2:
            theme = st.selectbox("主题风格", ["深色政务科技风", "浅色简洁风"], index=0 if cfg["主题风格"].startswith("深色") else 1)
            email_on = st.checkbox("开启邮件通知", value=cfg["邮件通知"])
            sms_on = st.checkbox("开启短信通知", value=cfg["短信通知"])
        saved = st.form_submit_button("保存配置", use_container_width=True)

    if saved:
        st.session_state["sys_config"] = {
            "平台名称": platform_name,
            "数据刷新周期(秒)": refresh,
            "告警阈值(%)": alert_threshold,
            "主题风格": theme,
            "邮件通知": email_on,
            "短信通知": sms_on,
        }
        st.toast("系统配置已保存")

    st.markdown("#### 当前生效配置")
    st.json(st.session_state["sys_config"])


def main() -> None:
    """系统管理页面主流程。"""
    sidebar.setup_page("智慧政务大数据平台 · 系统管理")
    utils.render_section_title("系统管理", "用户管理与系统运行配置")

    tab1, tab2 = st.tabs(["用户管理", "系统配置"])
    with tab1:
        render_user_management()
    with tab2:
        render_system_config()


if __name__ == "__main__":
    main()
