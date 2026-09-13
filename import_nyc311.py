"""
将 NYC 311 热线工单数据接入项目，生成真实诉求表 + 办件表 + 部门表 + 区域表。

用法：
    python import_nyc311.py <311的CSV路径> [--sample 50000] [--no-translate]

示例：
    python import_nyc311.py "D:/311_Service_Requests_from_2010_to_Present.csv" --sample 50000

说明：
    - 默认抽样 5 万行，输出 4 张表到 data/：
        appeals.csv（诉求）  cases.csv（办件）  departments.csv（部门）  regions.csv（区域）
    - 同一份 311 数据拆成「诉求」和「办件」两个业务视角
    - 默认把分类/区域/部门翻译成中文，--no-translate 可关闭
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"
RANDOM_SEED = 42

# 311 标准列 -> 项目 appeals 表字段
COLUMN_MAP = {
    "Unique Key": "appeal_id",
    "Complaint Type": "category",
    "Descriptor": "content",
    "Borough": "region",
    "Status": "status",
    "Created Date": "create_time",
    "Closed Date": "resolve_time",
}

STATUS_MAP = {
    "Closed": "已办结",
    "Open": "办理中",
    "Pending": "待审批",
    "In Progress": "办理中",
}

# 中文翻译（常见分类 + 行政区 + 部门）
CATEGORY_ZH = {
    "Blocked Driveway": "堵塞车道",
    "Illegal Parking": "违章停车",
    "Noise - Commercial": "商业噪音",
    "Noise - Street/Sidewalk": "街道噪音",
    "Derelict Vehicle": "废弃车辆",
    "Noise - Vehicle": "车辆噪音",
    "Noise - House of Worship": "宗教场所噪音",
    "Noise - Park": "公园噪音",
    "Illegal Dumping": "非法倾倒",
    "Dirty Condition": "环境卫生",
    "Graffiti": "乱涂乱画",
    "Broken Muni Meter": "停车收费表故障",
    "Street Condition": "道路破损",
    "Street Light Condition": "路灯故障",
    "Traffic Signal Condition": "信号灯故障",
    "Sewer": "下水道问题",
    "Water System": "供水问题",
    "Rodent": "鼠患治理",
    "Sanitation Condition": "环卫问题",
}

REGION_ZH = {
    "BROOKLYN": "布鲁克林区",
    "QUEENS": "皇后区",
    "MANHATTAN": "曼哈顿区",
    "BRONX": "布朗克斯区",
    "STATEN ISLAND": "史泰登岛区",
}

AGENCY_ZH = {
    "NYPD": "市警察局",
    "DOT": "市交通局",
    "DSNY": "市环卫局",
    "DOB": "市建筑局",
    "DEP": "市环保局",
    "HPD": "市住房局",
    "DOF": "市财政局",
    "DOHMH": "市卫生局",
    "DHS": "市无家可归者服务局",
    "PARKS": "市公园局",
}

HANDLERS = ["张伟", "李娜", "王强", "刘洋", "陈静", "赵磊", "孙敏", "周涛", "吴芳", "郑丽"]


def _find_column(df: pd.DataFrame, key: str) -> str | None:
    if key in df.columns:
        return key
    for alias in {
        "Unique Key": ["unique_key", "UniqueKey"],
        "Complaint Type": ["complaint_type", "complaintType"],
        "Descriptor": ["descriptor"],
        "Borough": ["borough"],
        "Status": ["status"],
        "Created Date": ["created_date", "createdDate", "opened_dt"],
        "Closed Date": ["closed_date", "closedDate"],
        "Agency": ["agency"],
        "Agency Name": ["agency_name", "agencyName"],
    }.get(key, []):
        if alias in df.columns:
            return alias
    return None


def _hours_between(created, closed) -> float | None:
    """计算办结时长（小时），任一为空返回 None。"""
    if pd.isna(created) or pd.isna(closed):
        return None
    return round((closed - created).total_seconds() / 3600, 1)


def main() -> None:
    parser = argparse.ArgumentParser(description="导入 NYC 311 数据")
    parser.add_argument("csv", help="311 CSV 文件路径")
    parser.add_argument("--sample", type=int, default=50000, help="抽样行数（0 表示全量）")
    parser.add_argument("--no-translate", action="store_true", help="不翻译成中文")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"文件不存在：{csv_path}")
        sys.exit(1)

    random.seed(RANDOM_SEED)
    zh = not args.no_translate
    cat = (lambda x: CATEGORY_ZH.get(x, x)) if zh else (lambda x: x)
    reg = (lambda x: REGION_ZH.get(x, x)) if zh else (lambda x: x)
    ag = (lambda x: AGENCY_ZH.get(x, x)) if zh else (lambda x: x)

    print(f"读取：{csv_path.name}")
    # 先读表头确定列名
    header = pd.read_csv(csv_path, nrows=0)
    cols = {k: _find_column(header, k) for k in list(COLUMN_MAP) + ["Agency", "Agency Name"]}
    missing = [k for k, v in cols.items() if v is None]
    if missing:
        print("缺少列，请把实际列名发我：", missing)
        sys.exit(1)
    usecols = [v for v in cols.values() if v]

    # 只读需要的列，按时间倒序取「最近」的 N 行（否则 nrows 取的是文件头部=最旧数据，今日办件量为 0）
    df = pd.read_csv(csv_path, usecols=usecols, low_memory=False)
    created_col = cols["Created Date"]
    df[created_col] = pd.to_datetime(df[created_col], errors="coerce", format="mixed")
    df = df.sort_values(created_col, ascending=False)
    df = df.head(args.sample if args.sample > 0 else len(df))

    # 将日期平移，使最新日期对齐「今天」，让今日办件量 / 近 7 天趋势有意义（历史数据演示处理）
    latest = df[created_col].max()
    if pd.notna(latest):
        shift_days = (pd.Timestamp.now().normalize() - latest.normalize()).days
        if shift_days > 0:
            df[created_col] = df[created_col] + pd.Timedelta(days=shift_days)
            df[cols["Closed Date"]] = (
                pd.to_datetime(df[cols["Closed Date"]], errors="coerce", format="mixed")
                + pd.Timedelta(days=shift_days)
            )
    print(f"共 {len(df):,} 行（日期已对齐到今天，最新 {df[created_col].max()}）")

    created = df[created_col]
    closed = pd.to_datetime(df[cols["Closed Date"]], errors="coerce", format="mixed")
    category_raw = df[cols["Complaint Type"]].fillna("其他")
    borough_raw = df[cols["Borough"]].fillna("未知区域")
    agency_raw = df[cols["Agency Name"]].fillna(df[cols["Agency"]]).fillna("市政部门")
    status_raw = df[cols["Status"]].astype(str)
    unique_key = df[cols["Unique Key"]].fillna(pd.Series(range(len(df)))).astype(str)

    category = category_raw.map(cat)
    region = borough_raw.map(reg)
    agency = agency_raw.map(ag)
    status = status_raw.map(STATUS_MAP).fillna("办理中")
    duration = [_hours_between(c, cl) for c, cl in zip(created, closed)]

    # ---------- 1. 诉求表 appeals ----------
    appeals = pd.DataFrame({
        "appeal_id": unique_key,
        "content": df[cols["Descriptor"]].fillna(category_raw).map(cat),
        "category": category,
        "region": region,
        "status": status,
        "is_overdue": 0,
        "create_time": created.dt.strftime("%Y-%m-%d %H:%M:%S"),
        "resolve_time": closed.dt.strftime("%Y-%m-%d %H:%M:%S"),
    }).dropna(subset=["create_time"])

    # ---------- 2. 办件表 cases ----------
    cases = pd.DataFrame({
        "case_id": [f"BJ{i:07d}" for i in range(1, len(df) + 1)],
        "title": "311 工单：" + category,
        "department": agency,
        "region": region,
        "item_type": category,
        "status": status,
        "urgency": [random.choice(["紧急", "高", "中", "低"]) for _ in range(len(df))],
        "handler": [random.choice(HANDLERS) for _ in range(len(df))],
        "submit_time": created.dt.strftime("%Y-%m-%d %H:%M:%S"),
        "finish_time": closed.dt.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_hours": duration,
        "satisfaction": [round(random.uniform(3.0, 5.0), 1) if d is not None else None for d in duration],
    }).dropna(subset=["submit_time"])

    # ---------- 3. 部门表 departments ----------
    agency_counts = agency.value_counts().reset_index()
    agency_counts.columns = ["name", "count"]
    departments = pd.DataFrame({
        "department_code": [f"DEPT{i + 1:03d}" for i in range(len(agency_counts))],
        "department_name": agency_counts["name"],
        "department_type": "公共服务",
        "responsibility": "负责相关市政事项的受理与处置",
        "employee_count": [random.randint(30, 300) for _ in range(len(agency_counts))],
    })

    # ---------- 4. 区域表 regions ----------
    region_counts = region.value_counts().reset_index()
    region_counts.columns = ["name", "count"]
    n = len(region_counts)
    regions = pd.DataFrame({
        "region_code": [f"REG{i + 1:03d}" for i in range(n)],
        "region_name": region_counts["name"],
        "population_wan": [random.randint(30, 200) for _ in range(n)],
        "area_km2": [random.randint(50, 300) for _ in range(n)],
        "map_x": [int(50 + 38 * math.cos(2 * math.pi * i / n)) for i in range(n)],
        "map_y": [int(50 + 38 * math.sin(2 * math.pi * i / n)) for i in range(n)],
    })

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    appeals.to_csv(DATA_DIR / "appeals.csv", index=False, encoding="utf-8-sig")
    cases.to_csv(DATA_DIR / "cases.csv", index=False, encoding="utf-8-sig")
    departments.to_csv(DATA_DIR / "departments.csv", index=False, encoding="utf-8-sig")
    regions.to_csv(DATA_DIR / "regions.csv", index=False, encoding="utf-8-sig")

    # ---------- 5. 写入 SQLite（让后端 FastAPI 也读到同一份真实数据） ----------
    import sqlite3
    from generate_data import generate_audit_logs, generate_inspections

    # 311 数据没有「巡查」「操作日志」，这两张用模拟数据补齐（系统内部数据）
    inspections = generate_inspections()
    audit_logs = generate_audit_logs()
    db_path = DATA_DIR / "gov_data.db"
    conn = sqlite3.connect(db_path)
    try:
        for name, tbl in [
            ("appeals", appeals), ("cases", cases), ("departments", departments),
            ("regions", regions), ("inspections", inspections), ("audit_logs", audit_logs),
        ]:
            tbl.to_sql(name, conn, if_exists="replace", index=False)
    finally:
        conn.close()

    print("\n完成！已生成 4 张真实数据表 + SQLite（6 张表）：")
    print(f"  - data/appeals.csv    （诉求，{len(appeals):,} 行）")
    print(f"  - data/cases.csv      （办件，{len(cases):,} 行）")
    print(f"  - data/departments.csv（部门，{len(departments)} 个）")
    print(f"  - data/regions.csv    （区域，{len(regions)} 个）")
    print(f"  - data/gov_data.db    （SQLite，后端可直接读取）")
    print("\n诉求分类 TOP5：")
    print(appeals["category"].value_counts().head(5).to_string())
    print("\n部门办件量 TOP5：")
    print(cases["department"].value_counts().head(5).to_string())
    print("\n现在 `cd dashboard && streamlit run app.py` 查看真实数据。")


if __name__ == "__main__":
    main()
