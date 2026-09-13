"""
图表生成模块（ECharts）。

通过 Streamlit 组件 iframe 内嵌 ECharts（CDN 加载），每个图表自带：
    - 深蓝渐变面板底色 + 青色描边圆角边框
    - 金色四角直角包边
    - 深色主题、中文字体、统一配色

所有函数返回 ECharts option 字典，由 render_chart() 统一渲染为面板。
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pandas as pd
import streamlit.components.v1 as components

# ---------------------------------------------------------------------------
# 主题常量
# ---------------------------------------------------------------------------
COLOR_BG = "#061226"
COLOR_CARD = "#0f2038"
COLOR_GOLD = "#fbbf24"
COLOR_CYAN = "#22d3ee"
COLOR_BLUE = "#4f8cff"
COLOR_GREEN = "#34d399"
COLOR_TEXT = "#e6f1ff"
COLOR_MUTED = "#8aa3c4"

FONT = '"Microsoft YaHei","PingFang SC","Hiragino Sans GB","Noto Sans CJK SC",sans-serif'

CHART_COLORS = [
    "#22d3ee", "#fbbf24", "#4f8cff", "#34d399",
    "#f472b6", "#a78bfa", "#f87171", "#2dd4bf", "#fb923c", "#60a5fa",
]

# ECharts CDN 地址（5.4.3 稳定版，作为离线缺失时的回退）
ECHARTS_CDN = "https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"

# 本地 ECharts 文件（离线优先），运行 `python download_echarts.py` 下载
ECHARTS_LOCAL = Path(__file__).resolve().parent.parent / "assets" / "echarts.min.js"
_echarts_cache: str | None = None


def _load_local_echarts() -> str:
    """读取本地 echarts.min.js（模块级缓存）。

    Returns:
        str: 本地 ECharts JS 内容；文件不存在时返回空串（此时回退 CDN）。
    """
    global _echarts_cache
    if _echarts_cache is None:
        _echarts_cache = (
            ECHARTS_LOCAL.read_text(encoding="utf-8") if ECHARTS_LOCAL.exists() else ""
        )
    return _echarts_cache


# ---------------------------------------------------------------------------
# 通用配置片段
# ---------------------------------------------------------------------------
def _title(text: str, subtext: str = "") -> dict:
    """生成左对齐标题配置。"""
    cfg = {
        "text": text,
        "left": 16,
        "top": 14,
        "textStyle": {
            "color": COLOR_TEXT,
            "fontSize": 15,
            "fontWeight": "bold",
            "fontFamily": FONT,
        },
    }
    if subtext:
        cfg["subtext"] = subtext
        cfg["subtextStyle"] = {"color": COLOR_MUTED, "fontSize": 11, "fontFamily": FONT}
        cfg["itemGap"] = 6
    return cfg


def _tooltip(trigger: str = "axis") -> dict:
    """生成深色 tooltip 配置。"""
    return {
        "trigger": trigger,
        "backgroundColor": "rgba(8,20,38,0.95)",
        "borderColor": "rgba(34,211,238,0.4)",
        "borderWidth": 1,
        "padding": [8, 12],
        "textStyle": {"color": COLOR_TEXT, "fontSize": 12, "fontFamily": FONT},
    }


def _legend(data: list, orient: str = "horizontal", top: int = 16) -> dict:
    """生成深色图例配置。"""
    return {
        "data": data,
        "orient": orient,
        "top": top,
        "right": 22,
        "itemWidth": 14,
        "itemHeight": 8,
        "textStyle": {"color": COLOR_MUTED, "fontSize": 11, "fontFamily": FONT},
    }


def _grid() -> dict:
    """生成统一网格边距。"""
    return {"left": 46, "right": 24, "top": 56, "bottom": 30, "containLabel": True}


def _cat_axis(data: list = None) -> dict:
    """生成类目轴配置。"""
    axis = {
        "type": "category",
        "boundaryGap": True,
        "axisLine": {"lineStyle": {"color": "rgba(34,211,238,0.28)"}},
        "axisTick": {"show": False},
        "axisLabel": {"color": COLOR_MUTED, "fontSize": 11, "fontFamily": FONT},
    }
    if data is not None:
        axis["data"] = data
    return axis


def _val_axis() -> dict:
    """生成数值轴配置。"""
    return {
        "type": "value",
        "axisLabel": {"color": COLOR_MUTED, "fontSize": 11, "fontFamily": FONT},
        "splitLine": {"lineStyle": {"color": "rgba(34,211,238,0.10)", "type": "dashed"}},
    }


def _frame() -> list:
    """生成面板边框 + 四角直角包边的 graphic 元素。"""
    c = COLOR_GOLD
    L = 13

    def line(x1, y1, x2, y2):
        return {
            "type": "line",
            "shape": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
            "style": {"stroke": c, "lineWidth": 2},
            "silent": True,
        }

    return [
        {
            "type": "rect", "left": 0, "right": 0, "top": 0, "bottom": 0,
            "shape": {"r": 6},
            "style": {"stroke": "rgba(34,211,238,0.22)", "lineWidth": 1, "fill": "transparent"},
            "silent": True,
            "z": 100,
        },
        {"type": "group", "left": 2, "top": 2, "z": 101, "children": [line(0, 0, L, 0), line(0, 0, 0, L)]},
        {"type": "group", "right": 2, "top": 2, "z": 101, "children": [line(-L, 0, 0, 0), line(0, 0, 0, L)]},
        {"type": "group", "left": 2, "bottom": 2, "z": 101, "children": [line(0, 0, L, 0), line(0, -L, 0, 0)]},
        {"type": "group", "right": 2, "bottom": 2, "z": 101, "children": [line(-L, 0, 0, 0), line(0, -L, 0, 0)]},
    ]


def _panel_bg() -> dict:
    """生成面板渐变背景。"""
    return {
        "type": "linear", "x": 0, "y": 0, "x2": 1, "y2": 1,
        "colorStops": [
            {"offset": 0, "color": "rgba(16,34,60,0.92)"},
            {"offset": 1, "color": "rgba(8,19,37,0.85)"},
        ],
    }


# ---------------------------------------------------------------------------
# 折线 / 面积图
# ---------------------------------------------------------------------------
def trend_line(trend_df: pd.DataFrame, title: str = "全市政务办件趋势（近7天）") -> dict:
    """办件趋势折线图（含渐变面积填充与发光主线）。"""
    dates = [d.strftime("%m-%d") for d in trend_df["date"]]
    counts = [int(v) for v in trend_df["count"]]
    finished = [int(v) for v in trend_df["finished_count"]]
    return {
        "title": _title(title),
        "tooltip": _tooltip("axis"),
        "legend": _legend(["办件量", "已办结"]),
        "grid": _grid(),
        "xAxis": _cat_axis(dates),
        "yAxis": _val_axis(),
        "series": [
            {
                "name": "办件量", "type": "line", "smooth": True,
                "symbol": "circle", "symbolSize": 7,
                "data": counts,
                "lineStyle": {"width": 3, "color": COLOR_CYAN,
                              "shadowColor": "rgba(34,211,238,0.55)", "shadowBlur": 12},
                "itemStyle": {"color": COLOR_CYAN, "borderColor": COLOR_BG, "borderWidth": 1.5},
                "areaStyle": {
                    "color": {
                        "type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                        "colorStops": [
                            {"offset": 0, "color": "rgba(34,211,238,0.32)"},
                            {"offset": 1, "color": "rgba(34,211,238,0.02)"},
                        ],
                    }
                },
            },
            {
                "name": "已办结", "type": "line", "smooth": True, "symbol": "none",
                "data": finished,
                "lineStyle": {"width": 2, "color": COLOR_GOLD, "type": "dashed"},
            },
        ],
    }


def appeal_trend_line(trend_df: pd.DataFrame, title: str = "群众诉求趋势（近14天）") -> dict:
    """群众诉求趋势折线图。"""
    dates = [d.strftime("%m-%d") for d in trend_df["date"]]
    counts = [int(v) for v in trend_df["count"]]
    return {
        "title": _title(title),
        "tooltip": _tooltip("axis"),
        "grid": _grid(),
        "xAxis": _cat_axis(dates),
        "yAxis": _val_axis(),
        "series": [
            {
                "name": "诉求量", "type": "line", "smooth": True,
                "symbol": "circle", "symbolSize": 6,
                "data": counts,
                "lineStyle": {"width": 3, "color": COLOR_GOLD,
                              "shadowColor": "rgba(251,191,36,0.5)", "shadowBlur": 12},
                "itemStyle": {"color": COLOR_GOLD, "borderColor": COLOR_BG, "borderWidth": 1.5},
                "areaStyle": {
                    "color": {
                        "type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                        "colorStops": [
                            {"offset": 0, "color": "rgba(251,191,36,0.30)"},
                            {"offset": 1, "color": "rgba(251,191,36,0.02)"},
                        ],
                    }
                },
            }
        ],
    }


def forecast_line(forecast: dict, title: str = "办件量趋势预测（Holt-Winters）") -> dict:
    """办件量趋势预测图（实际 + Holt-Winters 拟合 + 未来预测）。"""
    dates = [d.strftime("%m-%d") for d in forecast["dates"]] + [d.strftime("%m-%d") for d in forecast["future_dates"]]
    actual = forecast["actual"] + [None] * len(forecast["future_dates"])
    fitted = forecast.get("fitted", [None] * len(forecast["dates"])) + [None] * len(forecast["future_dates"])
    predicted = [None] * len(forecast["dates"]) + forecast["predicted"]
    return {
        "title": _title(title),
        "tooltip": _tooltip("axis"),
        "legend": _legend(["实际办件量", "Holt-Winters 拟合", "未来预测"]),
        "grid": _grid(),
        "xAxis": _cat_axis(dates),
        "yAxis": _val_axis(),
        "series": [
            {"name": "实际办件量", "type": "line", "smooth": True, "symbol": "circle", "symbolSize": 5,
             "data": actual, "lineStyle": {"width": 3, "color": COLOR_CYAN, "shadowBlur": 10, "shadowColor": "rgba(34,211,238,0.5)"},
             "itemStyle": {"color": COLOR_CYAN}},
            {"name": "Holt-Winters 拟合", "type": "line", "smooth": True, "symbol": "none",
             "data": fitted, "lineStyle": {"width": 2, "color": COLOR_GOLD, "type": "dashed"}},
            {"name": "未来预测", "type": "line", "smooth": True, "symbol": "circle", "symbolSize": 5,
             "data": predicted, "lineStyle": {"width": 3, "color": COLOR_GREEN, "type": "dashed"},
             "itemStyle": {"color": COLOR_GREEN}},
        ],
    }


# ---------------------------------------------------------------------------
# 条形图
# ---------------------------------------------------------------------------
def top_items_bar(top_df: pd.DataFrame, title: str = "高频事项 TOP5") -> dict:
    """高频事项水平条形图（渐变金青色）。"""
    names = top_df["item_type"].tolist()[::-1]
    counts = [int(v) for v in top_df["count"].tolist()[::-1]]
    return {
        "title": _title(title),
        "tooltip": _tooltip("axis"),
        "grid": _grid(),
        "xAxis": _val_axis(),
        "yAxis": _cat_axis(names),
        "series": [
            {
                "name": "办件量", "type": "bar", "data": counts, "barWidth": 14,
                "itemStyle": {
                    "borderRadius": [0, 7, 7, 0],
                    "color": {
                        "type": "linear", "x": 0, "y": 0, "x2": 1, "y2": 0,
                        "colorStops": [{"offset": 0, "color": "#0e7ea8"}, {"offset": 1, "color": COLOR_GOLD}],
                    },
                },
                "label": {"show": True, "position": "right", "color": COLOR_TEXT, "fontSize": 11},
            }
        ],
    }


def department_ranking_bar(rank_df: pd.DataFrame, title: str = "部门效能排名") -> dict:
    """部门效能排名水平条形图。"""
    data = rank_df.sort_values("score", ascending=True)
    names = data["department"].tolist()
    scores = [round(float(v), 1) for v in data["score"]]
    return {
        "title": _title(title),
        "tooltip": _tooltip("axis"),
        "grid": _grid(),
        "xAxis": _val_axis(),
        "yAxis": _cat_axis(names),
        "series": [
            {
                "name": "效能得分", "type": "bar", "data": scores, "barWidth": 12,
                "itemStyle": {
                    "borderRadius": [0, 6, 6, 0],
                    "color": {
                        "type": "linear", "x": 0, "y": 0, "x2": 1, "y2": 0,
                        "colorStops": [{"offset": 0, "color": "#145c86"}, {"offset": 1, "color": COLOR_CYAN}],
                    },
                },
                "label": {"show": True, "position": "right", "color": COLOR_TEXT, "fontSize": 11},
            }
        ],
    }


# ---------------------------------------------------------------------------
# 饼图 / 环形图
# ---------------------------------------------------------------------------
def appeal_category_donut(cat_df: pd.DataFrame, title: str = "诉求分类占比") -> dict:
    """诉求分类环形图（含中心文字）。"""
    data = [{"name": r["category"], "value": int(r["count"])} for _, r in cat_df.iterrows()]
    return {
        "title": _title(title),
        "tooltip": _tooltip("item"),
        "legend": _legend([r["category"] for _, r in cat_df.iterrows()], orient="vertical", top="middle"),
        "graphic": [
            {
                "type": "text", "left": "34%", "top": "44%",
                "style": {"text": "诉求分类", "fill": COLOR_MUTED, "fontSize": 13, "fontFamily": FONT},
            }
        ],
        "series": [
            {
                "name": "诉求分类", "type": "pie",
                "radius": ["48%", "70%"], "center": ["34%", "50%"],
                "data": data,
                "itemStyle": {"borderColor": COLOR_BG, "borderWidth": 2, "borderRadius": 4},
                "label": {"color": COLOR_MUTED, "fontSize": 11, "fontFamily": FONT},
                "labelLine": {"lineStyle": {"color": "rgba(138,163,196,0.4)"}},
            }
        ],
    }


# ---------------------------------------------------------------------------
# 地图类（示意坐标气泡图，无需地图服务，可离线渲染）
# ---------------------------------------------------------------------------
def region_heatmap(region_heat_df: pd.DataFrame, title: str = "全市诉求分布热力") -> dict:
    """全市诉求分布气泡图（区域坐标 + 诉求量，含颜色图例）。"""
    maxc = int(region_heat_df["appeal_count"].max()) or 1
    data = [
        {"name": r["region_name"], "value": [int(r["map_x"]), int(r["map_y"]), int(r["appeal_count"])]}
        for _, r in region_heat_df.iterrows()
    ]
    sizes = [18 + 46 * (int(r["appeal_count"]) / maxc) for _, r in region_heat_df.iterrows()]
    return {
        "title": _title(title),
        "tooltip": _tooltip("item"),
        "xAxis": {"type": "value", "min": 0, "max": 100, "show": False},
        "yAxis": {"type": "value", "min": 0, "max": 100, "show": False},
        "visualMap": {
            "min": 0, "max": maxc, "dimension": 2,
            "orient": "vertical", "right": 12, "top": "center",
            "text": ["高", "低"],
            "textStyle": {"color": COLOR_MUTED, "fontSize": 11},
            "inRange": {"color": ["rgba(34,211,238,0.35)", COLOR_GOLD]},
        },
        "series": [
            {
                "name": "诉求量", "type": "scatter", "data": data, "symbolSize": sizes,
                "itemStyle": {"borderColor": "rgba(255,255,255,0.35)", "borderWidth": 1},
                "label": {"show": True, "formatter": "{b}", "position": "top",
                          "color": COLOR_TEXT, "fontSize": 11, "fontFamily": FONT},
            }
        ],
    }


def city_map(regions: pd.DataFrame, events: pd.DataFrame, title: str = "城市一张图 · 事件点位") -> dict:
    """城市一张图（区域中心 + 巡查事件涟漪点位）。"""
    centers = [{"name": r["region_name"], "value": [int(r["map_x"]), int(r["map_y"])]} for _, r in regions.iterrows()]

    type_list = events["inspection_type"].unique().tolist()
    color_map = {t: CHART_COLORS[i % len(CHART_COLORS)] for i, t in enumerate(type_list)}

    series = [
        {
            "name": "区域", "type": "scatter", "data": centers, "symbolSize": 28, "z": 1,
            "itemStyle": {"color": "rgba(34,211,238,0.10)", "borderColor": "rgba(34,211,238,0.55)", "borderWidth": 1.5},
            "label": {"show": True, "formatter": "{b}", "position": "top",
                      "color": COLOR_TEXT, "fontSize": 11, "fontFamily": FONT},
            "tooltip": {"show": False},
        }
    ]

    for itype in type_list:
        sub = events[events["inspection_type"] == itype].reset_index(drop=True)
        pts = [
            {"name": row["region"],
             "value": [int(row["map_x"]) + (i % 5 - 2) * 1.6, int(row["map_y"]) + (i % 3 - 1) * 1.6]}
            for i, (_, row) in enumerate(sub.iterrows())
        ]
        series.append(
            {
                "name": itype, "type": "effectScatter", "data": pts, "symbolSize": 8, "z": 2,
                "rippleEffect": {"scale": 3.6, "brushType": "stroke"},
                "itemStyle": {"color": color_map[itype], "shadowBlur": 8, "shadowColor": color_map[itype]},
            }
        )

    return {
        "title": _title(title),
        "tooltip": _tooltip("item"),
        "legend": _legend(type_list, top="bottom"),
        "xAxis": {"type": "value", "min": 0, "max": 100, "show": False},
        "yAxis": {"type": "value", "min": 0, "max": 100, "show": False},
        "series": series,
    }


# ---------------------------------------------------------------------------
# 渲染入口
# ---------------------------------------------------------------------------
def render_chart(option: dict, height: int = 320) -> None:
    """将 ECharts option 渲染为带包边面板的图表组件。

    Args:
        option (dict): ECharts option 字典（不含面板背景/边框，由本函数统一附加）。
        height (int): 图表高度（像素）。
    """
    option = dict(option)
    option["backgroundColor"] = _panel_bg()
    # 合并自定义 graphic（如环形图中心文字）与面板边框
    extra = option.get("graphic", [])
    option["graphic"] = _frame() + extra

    cid = f"ec_{uuid.uuid4().hex[:8]}"
    option_json = json.dumps(option, ensure_ascii=False).replace("</", "<\\/")

    # 离线优先：本地存在 echarts.min.js 则内联，否则回退 CDN
    local_js = _load_local_echarts()
    if local_js:
        echarts_tag = "<script>" + local_js + "</script>"
    else:
        echarts_tag = f'<script src="{ECHARTS_CDN}"></script>'

    # 初始化脚本用占位符替换，避免与 ECharts JS 中的花括号冲突
    init_script = (
        "<script>(function(){"
        "var el=document.getElementById('__CID__');"
        "if(typeof echarts==='undefined'){"
        "el.innerHTML='<div style=\"display:flex;align-items:center;justify-content:center;height:100%;"
        "color:#8aa3c4;font-size:13px;\">图表组件加载失败，请运行 python download_echarts.py 或检查网络</div>';"
        "return;}"
        "var chart=echarts.init(el);"
        "chart.setOption(__OPTION__);"
        "window.addEventListener('resize',function(){chart.resize();});"
        "})();</script>"
    )
    init_script = init_script.replace("__CID__", cid).replace("__OPTION__", option_json)

    html = (
        "<style>body{margin:0;background:transparent;}</style>"
        f'<div id="{cid}" style="width:100%;height:{height}px;"></div>'
        + echarts_tag
        + init_script
    )
    components.html(html, height=height, scrolling=False)
