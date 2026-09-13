"""
侧边栏导航配置模块。

Streamlit 的 pages/ 目录会自动生成左侧多页面导航；
本模块在其基础上补充「品牌区」与「底部信息」，并统一定义导航说明。
"""

from __future__ import annotations

import streamlit as st

from src import __version__, utils
from src.utils import COLOR_GOLD, COLOR_CYAN, COLOR_TEXT, COLOR_MUTED


def setup_page(title: str) -> None:
    """页面统一初始化：页面配置 + CSS 注入 + 侧边栏品牌区/导航说明/底部。

    Args:
        title (str): 页面标题。
    """
    utils.set_page_config(title)
    utils.load_css()
    render_header()
    render_nav_hint()
    render_footer()
    utils.render_top_bar()


def render_header() -> None:
    """在侧边栏顶部渲染平台品牌区（Logo + 标题 + 副标题）。"""
    st.sidebar.markdown(
        utils.clean_html(
            f"""
            <div style="display:flex;align-items:center;gap:10px;padding:8px 4px 14px 4px;
                        border-bottom:1px solid #1e3a5f;margin-bottom:10px;">
                <div style="width:42px;height:42px;border-radius:10px;
                            background:linear-gradient(135deg,{COLOR_GOLD},{COLOR_CYAN});
                            display:flex;align-items:center;justify-content:center;
                            flex-shrink:0;">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M4 21h16"/>
                        <path d="M6 21V10l6-4 6 4v11"/>
                        <path d="M10 21v-6h4v6"/>
                    </svg>
                </div>
                <div>
                    <div style="font-size:1.02rem;font-weight:800;color:{COLOR_TEXT};line-height:1.2;">
                        智慧政务大数据平台
                    </div>
                    <div style="font-size:0.72rem;color:{COLOR_MUTED};margin-top:2px;">
                        一屏统览 · 一网通办 · 一网统管
                    </div>
                </div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


def render_nav_hint() -> None:
    """在侧边栏渲染导航分组说明（提示当前为一屏统览等 7 大模块）。"""
    st.sidebar.markdown(
        utils.clean_html(
            f"""
            <div style="font-size:0.7rem;color:{COLOR_MUTED};padding:4px 4px 2px 4px;">
                ▸ 七大模块导航
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    """在侧边栏底部渲染版本信息与版权说明。"""
    st.sidebar.markdown(
        utils.clean_html(
            f"""
            <div style="margin-top:16px;padding-top:10px;border-top:1px solid #1e3a5f;
                        font-size:0.7rem;color:{COLOR_MUTED};line-height:1.6;">
                <div>版本 v{__version__}</div>
                <div>© 2024 智慧政务大数据平台项目组</div>
                <div style="color:{COLOR_GOLD};">仅供学习与演示使用</div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )
