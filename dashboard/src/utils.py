"""
通用工具函数模块。

提供页面配置、CSS 注入、中文字体探测、主题色、顶部标题栏（含实时时钟）、
KPI 指标卡、格式化等能力，供首页与各业务页面复用，保证全站风格统一。
"""

from __future__ import annotations

import re
import textwrap
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

# ---------------------------------------------------------------------------
# 路径常量
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"
CSS_FILE = ASSETS_DIR / "style.css"

# ---------------------------------------------------------------------------
# 深色政务科技风主题色
# ---------------------------------------------------------------------------
COLOR_BG = "#061226"        # 主背景深蓝
COLOR_CARD = "#0f2038"      # 卡片背景
COLOR_PRIMARY = "#1a3a5c"   # 主色（深蓝）
COLOR_GOLD = "#FBBF24"      # 点缀色：金色
COLOR_CYAN = "#22D3EE"      # 点缀色：青色
COLOR_TEXT = "#E6F1FF"      # 正文文字
COLOR_MUTED = "#8AA3C4"     # 次要文字
COLOR_GRID = "#1e3a5f"      # 图表网格线

# 图表统一配色（与主题协调，按序循环使用）
CHART_COLORS = [
    "#22D3EE",  # 青
    "#FBBF24",  # 金
    "#4F8CFF",  # 蓝
    "#34D399",  # 绿
    "#F472B6",  # 粉
    "#A78BFA",  # 紫
    "#F87171",  # 红
    "#2DD4BF",  # 浅青绿
    "#FB923C",  # 橙
    "#60A5FA",  # 亮蓝
]


# ---------------------------------------------------------------------------
# 页面配置与样式
# ---------------------------------------------------------------------------
def set_page_config(title: str = "智慧政务大数据平台") -> None:
    """统一配置 Streamlit 页面属性。

    Args:
        title (str): 页面标题。
    """
    st.set_page_config(
        page_title=title,
        page_icon="◈",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def load_css() -> None:
    """读取并注入自定义深色政务风格 CSS。"""
    if CSS_FILE.exists():
        css = CSS_FILE.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def clean_html(html: str) -> str:
    """去除 HTML 字符串的缩进与首尾空白。

    Streamlit 的 markdown 会把带缩进的内容渲染为代码块，导致 HTML 源码直接
    显示在页面上；所有多行 HTML 统一通过本函数清洗后再渲染。
    """
    return textwrap.dedent(html).strip()


# ---------------------------------------------------------------------------
# 顶部标题栏（含实时时钟）
# ---------------------------------------------------------------------------
def render_top_bar() -> None:
    """渲染大屏顶部标题栏（平台名称 + 副标题 + 实时时钟）。

    使用 Streamlit 组件 iframe 承载原生 HTML + JS，实现每秒刷新的时钟。
    """
    html = """
    <style>
        * { box-sizing: border-box; }
        body { margin: 0; background: transparent; }
        .topbar {
            position: relative;
            display: flex;
            align-items: center;
            justify-content: space-between;
            height: 66px;
            padding: 0 22px;
            background:
                linear-gradient(90deg, rgba(9,24,46,0.2) 0%, rgba(19,48,86,0.85) 50%, rgba(9,24,46,0.2) 100%);
            border: 1px solid rgba(34,211,238,0.22);
            border-radius: 12px;
            overflow: hidden;
            color: #e6f1ff;
            font-family: "Microsoft YaHei","PingFang SC","Hiragino Sans GB",sans-serif;
        }
        .topbar::after {
            content: "";
            position: absolute;
            left: 0; right: 0; bottom: 0; height: 2px;
            background: linear-gradient(90deg, transparent, #fbbf24, #22d3ee, #fbbf24, transparent);
            opacity: 0.9;
        }
        .topbar .glow {
            position: absolute; top: -40px; left: 50%; transform: translateX(-50%);
            width: 500px; height: 80px; border-radius: 50%;
            background: rgba(34,211,238,0.14); filter: blur(28px); pointer-events: none;
        }
        .left { display: flex; align-items: center; gap: 12px; z-index: 1; }
        .logo {
            width: 42px; height: 42px; border-radius: 10px;
            background: linear-gradient(135deg, #fbbf24, #22d3ee);
            display: flex; align-items: center; justify-content: center;
            font-size: 22px; box-shadow: 0 0 16px rgba(34,211,238,0.5);
        }
        .title { font-size: 1.28rem; font-weight: 800; letter-spacing: 2px;
                 text-shadow: 0 0 16px rgba(34,211,238,0.5); }
        .subtitle { font-size: 0.72rem; color: #8aa3c4; letter-spacing: 1px; margin-top: 2px; }
        .right { display: flex; align-items: center; gap: 18px; z-index: 1; }
        .clock { font-size: 1.5rem; font-weight: 800; font-variant-numeric: tabular-nums;
                 color: #fbbf24; text-shadow: 0 0 14px rgba(251,191,36,0.55); letter-spacing: 1px; }
        .date { font-size: 0.78rem; color: #8aa3c4; text-align: right; line-height: 1.4; }
    </style>
    <div class="topbar">
        <div class="glow"></div>
        <div class="left">
            <div class="logo">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M4 21h16"/>
                    <path d="M6 21V10l6-4 6 4v11"/>
                    <path d="M10 21v-6h4v6"/>
                </svg>
            </div>
            <div>
                <div class="title">智慧政务大数据平台</div>
                <div class="subtitle">一屏统览 · 一网通办 · 一网统管 · 一网共享</div>
            </div>
        </div>
        <div class="right">
            <div class="date">
                <div id="date">----年--月--日</div>
                <div>城市运行态势感知中心</div>
            </div>
            <div class="clock" id="clock">--:--:--</div>
        </div>
    </div>
    <script>
    (function () {
        function pad(n) { return n < 10 ? '0' + n : '' + n; }
        var week = ['日', '一', '二', '三', '四', '五', '六'];
        function tick() {
            var d = new Date();
            var el1 = document.getElementById('clock');
            var el2 = document.getElementById('date');
            if (el1) el1.textContent = pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds());
            if (el2) el2.textContent = d.getFullYear() + '年' + pad(d.getMonth() + 1) + '月' + pad(d.getDate()) + '日 星期' + week[d.getDay()];
        }
        tick();
        setInterval(tick, 1000);
    })();
    </script>
    """
    components.html(html, height=66, scrolling=False)


# ---------------------------------------------------------------------------
# 页面模块标题
# ---------------------------------------------------------------------------
def render_section_title(title: str, subtitle: str = "") -> None:
    """渲染页面模块标题（左侧金色装饰线 + 渐变底色）。

    Args:
        title (str): 模块主标题。
        subtitle (str): 模块副标题（可选）。
    """
    subtitle_html = (
        f'<div class="s">{subtitle}</div>' if subtitle else ""
    )
    st.markdown(
        clean_html(
            f"""
            <div class="page-title">
                <div class="t">{title}</div>
                {subtitle_html}
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# KPI 指标卡
# ---------------------------------------------------------------------------
_KPI_META = {
    "today_count": {"label": "今日办件量", "color": "#22d3ee"},
    "avg_duration": {"label": "平均办理时长", "color": "#fbbf24"},
    "window_usage": {"label": "窗口使用率", "color": "#4f8cff"},
    "satisfaction": {"label": "群众满意度", "color": "#34d399"},
}


def render_kpi_cards(kpis: dict) -> None:
    """渲染首页 4 项核心 KPI 指标卡（直角包边 + 彩色标识点 + 环比箭头）。

    Args:
        kpis (dict): metrics.compute_kpis 的返回值。
    """
    cards = []
    for key, meta in _KPI_META.items():
        k = kpis[key]
        value = k["value"]
        delta = k["delta"]
        compare_label = k.get("label", "")
        delta_color = k.get("delta_color", "normal")

        # 将数值与单位拆分，便于大小字号排版
        m = re.match(r"^([\d,\.]+)(.*)$", str(value))
        num, unit = (m.group(1), m.group(2)) if m else (str(value), "")

        # 计算涨跌箭头与颜色（normal：涨为好；inverse：涨为坏）
        if isinstance(delta, (int, float)) and delta != 0:
            is_up = delta > 0
            is_good = (is_up and delta_color == "normal") or ((not is_up) and delta_color == "inverse")
            arrow = "▲" if is_up else "▼"
            color = "#34d399" if is_good else "#f87171"
            delta_html = f'<span class="kpi-delta" style="color:{color};">{arrow} {abs(delta)}</span>'
        else:
            delta_html = f'<span class="kpi-delta" style="color:{COLOR_MUTED};">— 持平</span>'

        # 卡片使用单行拼接，避免多行缩进被 markdown 渲染为代码块
        cards.append(
            f'<div class="kpi-card" style="--accent:{meta["color"]};'
            f'--accent-glow:{meta["color"]}44;--accent-bg:{meta["color"]}22;">'
            f'<span class="corner tl"></span><span class="corner tr"></span>'
            f'<span class="corner bl"></span><span class="corner br"></span>'
            f'<div class="kpi-head"><span class="kpi-dot" style="background:{meta["color"]};'
            f'box-shadow:0 0 8px {meta["color"]};"></span>'
            f'<span class="kpi-label">{meta["label"]}</span></div>'
            f'<div class="kpi-value">{num}<span class="kpi-unit">{unit}</span></div>'
            f'<div class="kpi-foot">{delta_html}<span class="kpi-desc">{compare_label}</span></div>'
            f'</div>'
        )

    st.markdown(f'<div class="kpi-grid">{"".join(cards)}</div>', unsafe_allow_html=True)
