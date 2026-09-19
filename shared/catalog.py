"""群众端业务分类与承办部门主数据。"""

from __future__ import annotations

BUSINESS_CATEGORIES = [
    {"name": "交通出行", "department": "市交通运输局"},
    {"name": "噪声扰民", "department": "市生态环境局"},
    {"name": "市容环境", "department": "市城市管理局"},
    {"name": "公共秩序", "department": "市公安局"},
    {"name": "社会救助", "department": "市民政局"},
    {"name": "动物管理", "department": "市农业农村局"},
]

DEPARTMENTS = [item["department"] for item in BUSINESS_CATEGORIES]
CATEGORY_DEPARTMENT = {item["name"]: item["department"] for item in BUSINESS_CATEGORIES}

_RAW_CATEGORY_MAP = {
    "堵塞车道": "交通出行",
    "违章停车": "交通出行",
    "废弃车辆": "交通出行",
    "Traffic": "交通出行",
    "Bike/Roller/Skate Chronic": "交通出行",
    "商业噪音": "噪声扰民",
    "街道噪音": "噪声扰民",
    "车辆噪音": "噪声扰民",
    "公园噪音": "噪声扰民",
    "宗教场所噪音": "噪声扰民",
    "Vending": "市容环境",
    "Posting Advertisement": "市容环境",
    "乱涂乱画": "市容环境",
    "Urinating in Public": "市容环境",
    "Drinking": "公共秩序",
    "Panhandling": "公共秩序",
    "Disorderly Youth": "公共秩序",
    "Illegal Fireworks": "公共秩序",
    "Homeless Encampment": "社会救助",
    "Animal Abuse": "动物管理",
}


def business_category(raw_category: str) -> str:
    """把 311 原始细分类归并为群众易理解的业务大类。"""
    value = (raw_category or "").strip()
    if value in CATEGORY_DEPARTMENT:
        return value
    return _RAW_CATEGORY_MAP.get(value, "市容环境")


def department_for_category(category: str) -> str:
    return CATEGORY_DEPARTMENT[business_category(category)]
