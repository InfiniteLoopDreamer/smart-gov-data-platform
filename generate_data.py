"""
智慧政务大数据平台 - 模拟数据生成脚本。

运行方式：
    python generate_data.py

功能说明：
    在 data/ 目录下一次性生成 6 张相互关联的 CSV 数据表，用于支撑整个平台演示。
    所有随机过程使用固定随机种子（random.seed(42) / np.random.seed(42)），
    保证每次运行生成的数据完全一致、可复现。

生成的数据表（6 张）：
    1. departments.csv   —— 部门信息表（部门维度）
    2. regions.csv       —— 区域信息表（区域维度，含示意地图坐标）
    3. cases.csv         —— 办件工单表（关联部门、区域、事项）
    4. appeals.csv       —— 群众诉求表（关联区域、诉求分类）
    5. inspections.csv   —— 综合巡查任务表（关联区域、巡查类型）
    6. audit_logs.csv    —— 操作审计日志表（关联操作用户）

数据关联关系：
    - 办件表(cases)      通过 department / region 关联部门表与区域表
    - 诉求表(appeals)    通过 region 关联区域表
    - 巡查表(inspections)通过 region 关联区域表
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# 全局配置
# ---------------------------------------------------------------------------
RANDOM_SEED = 42          # 固定随机种子，保证数据可复现
DATA_DIR = Path(__file__).resolve().parent / "data"
TODAY = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
DAYS_BACK = 60            # 数据覆盖近 60 天（含今日）

# ---------------------------------------------------------------------------
# 基础维度数据（常量池）
# ---------------------------------------------------------------------------
DEPARTMENTS = [
    ("DEPT001", "市公安局", "行政执法", "负责全市公共安全、户籍与交通秩序管理"),
    ("DEPT002", "市市场监管局", "行政执法", "负责市场主体登记、食品药品与质量监管"),
    ("DEPT003", "市人力资源和社会保障局", "公共服务", "负责就业、社保与劳动关系服务"),
    ("DEPT004", "市卫生健康委员会", "公共服务", "负责医疗卫生、公共卫生与健康服务"),
    ("DEPT005", "市住房和城乡建设局", "综合管理", "负责住房保障、工程建设与不动产管理"),
    ("DEPT006", "市自然资源和规划局", "综合管理", "负责国土空间规划、土地与自然资源管理"),
    ("DEPT007", "市税务局", "行政执法", "负责税收征管与纳税服务"),
    ("DEPT008", "市交通运输局", "综合管理", "负责道路运输、公共交通与物流管理"),
    ("DEPT009", "市教育局", "公共服务", "负责基础教育、招生考试与教育服务"),
    ("DEPT010", "市民政局", "公共服务", "负责社会救助、婚姻登记与养老服务"),
    ("DEPT011", "市生态环境局", "行政执法", "负责环境污染防治与生态保护"),
    ("DEPT012", "市城市管理局", "行政执法", "负责市容市貌与城市综合管理"),
]

REGIONS = [
    ("REG001", "城东区", 86.4, 132.5, 82, 38),
    ("REG002", "城西区", 72.1, 118.3, 16, 46),
    ("REG003", "城南区", 91.2, 156.7, 55, 14),
    ("REG004", "城北区", 68.7, 124.1, 48, 82),
    ("REG005", "高新区", 54.3, 98.6, 72, 62),
    ("REG006", "经开区", 47.8, 87.4, 28, 66),
    ("REG007", "滨湖区", 41.5, 76.2, 78, 26),
    ("REG008", "新城区", 59.6, 102.8, 32, 24),
]

# 高频办理事项（权重用于控制出现频率，模拟真实业务分布）
ITEM_TYPES = [
    ("企业开办", 16),
    ("社保参保登记", 13),
    ("公积金提取", 12),
    ("身份证办理", 11),
    ("驾驶证换证", 9),
    ("不动产登记", 10),
    ("营业执照年检", 8),
    ("出入境证件办理", 7),
    ("医保报销", 9),
    ("户籍迁移", 6),
    ("居住证办理", 7),
    ("生育津贴申领", 5),
]

CASE_STATUSES = ["已办结", "办理中", "待审批", "待受理", "已驳回"]
CASE_STATUS_WEIGHTS = [0.58, 0.15, 0.12, 0.08, 0.07]
URGENCY_LEVELS = ["紧急", "高", "中", "低"]
URGENCY_WEIGHTS = [0.08, 0.22, 0.45, 0.25]

APPEAL_CATEGORIES = [
    ("城市管理", "占道经营、违规搭建、噪音扰民"),
    ("交通出行", "道路拥堵、公交线路、停车难"),
    ("民生保障", "社保咨询、就业帮扶、困难救助"),
    ("生态环境", "空气污染、河道污染、垃圾清运"),
    ("市场监管", "消费投诉、食品安全、价格监督"),
    ("公共安全", "消防隐患、治安问题、应急求助"),
    ("教育医疗", "入学咨询、医保政策、看病挂号"),
    ("住房保障", "公租房申请、房屋维修、物业纠纷"),
]
APPEAL_STATUSES = ["已办结", "办理中", "已受理", "已督办"]

INSPECTION_TYPES = ["市容市貌", "安全生产", "食品安全", "消防安全", "环境污染", "交通秩序"]
INSPECTION_STATUSES = ["待巡查", "巡查中", "已完成"]
INSPECTION_STATUS_WEIGHTS = [0.18, 0.27, 0.55]

USERS = ["admin", "张伟", "李娜", "王强", "刘洋", "陈静", "赵磊", "孙敏", "周涛", "吴芳"]
MODULES = ["登录认证", "办件管理", "审批服务", "数据资源", "系统设置", "监督调度", "安全审计"]
OPERATIONS = {
    "登录认证": ["登录系统", "退出系统", "登录失败"],
    "办件管理": ["查询办件", "新增办件", "导出办件数据"],
    "审批服务": ["审批通过", "审批驳回", "退回补充材料"],
    "数据资源": ["查看数据资产", "下载数据预览", "申请数据服务"],
    "系统设置": ["新增用户", "修改用户权限", "修改系统配置"],
    "监督调度": ["查看督办工单", "发起督办", "关闭督办"],
    "安全审计": ["查看操作日志", "导出审计日志", "处理告警"],
}
LOG_LEVELS = ["INFO", "INFO", "INFO", "WARN", "ERROR"]  # 大部分为正常，少量告警

HANDLERS = [
    "张伟", "李娜", "王强", "刘洋", "陈静", "赵磊", "孙敏", "周涛", "吴芳",
    "郑丽", "冯军", "蒋红", "沈华", "韩梅", "杨光", "朱霞", "秦勇", "许静", "何平",
]


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------
def random_datetime(day_offset: int) -> datetime:
    """根据“距今天数”生成一个随机的具体时间点。

    Args:
        day_offset (int): 距离今天的偏移天数（0 表示今天）。

    Returns:
        datetime: 对应日期内的随机时间。
    """
    day = TODAY - timedelta(days=day_offset)
    return day + timedelta(
        hours=random.randint(8, 18),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )


def weighted_choice(pool: list, weights: list):
    """按权重从池中随机抽取一个元素。"""
    return random.choices(pool, weights=weights, k=1)[0]


# ---------------------------------------------------------------------------
# 各表生成函数
# ---------------------------------------------------------------------------
def generate_departments() -> pd.DataFrame:
    """生成部门信息表。"""
    rows = []
    for code, name, dtype, duty in DEPARTMENTS:
        rows.append(
            {
                "department_code": code,
                "department_name": name,
                "department_type": dtype,
                "responsibility": duty,
                "employee_count": random.randint(30, 260),
            }
        )
    return pd.DataFrame(rows)


def generate_regions() -> pd.DataFrame:
    """生成区域信息表（含示意地图坐标 x/y，用于“城市一张图”渲染）。"""
    rows = []
    for code, name, pop, area, x, y in REGIONS:
        rows.append(
            {
                "region_code": code,
                "region_name": name,
                "population_wan": pop,
                "area_km2": area,
                "map_x": x,
                "map_y": y,
            }
        )
    return pd.DataFrame(rows)


def generate_cases(n: int = 8000) -> pd.DataFrame:
    """生成办件工单表。

    Args:
        n (int): 生成的办件记录总数。

    Returns:
        pd.DataFrame: 办件工单数据。
    """
    item_names = [it[0] for it in ITEM_TYPES]
    item_weights = [it[1] for it in ITEM_TYPES]
    dept_names = [d[1] for d in DEPARTMENTS]
    region_names = [r[1] for r in REGIONS]

    rows = []
    for i in range(1, n + 1):
        # 办件编号：按年份 + 6 位序号
        case_id = f"BJ{TODAY.year}{i:06d}"

        item_type = weighted_choice(item_names, item_weights)
        dept = random.choice(dept_names)
        region = random.choice(region_names)
        status = weighted_choice(CASE_STATUSES, CASE_STATUS_WEIGHTS)
        urgency = weighted_choice(URGENCY_LEVELS, URGENCY_WEIGHTS)

        # 时间：近 60 天内，偏重近期以贴近真实业务节奏
        day_offset = random.choices(range(DAYS_BACK), weights=range(DAYS_BACK, 0, -1), k=1)[0]
        submit_time = random_datetime(day_offset)

        # 办理时长与满意度：已办结/已驳回有结果，在办工单暂无
        if status in ("已办结", "已驳回"):
            duration_hours = round(random.uniform(0.5, 48.0), 1)
            finish_time = submit_time + timedelta(hours=duration_hours)
            if status == "已办结":
                # 时长越短满意度越高，模拟真实相关性
                satisfaction = round(max(3.0, min(5.0, 5.0 - duration_hours / 24.0 + random.uniform(-0.2, 0.3))), 1)
            else:
                satisfaction = round(random.uniform(1.0, 2.5), 1)
        else:
            duration_hours = None
            finish_time = None
            satisfaction = None

        # 办件标题：事项 + 区域 + 办理人
        handler = random.choice(HANDLERS)
        title = f"{region}{item_type}申请办理"

        rows.append(
            {
                "case_id": case_id,
                "title": title,
                "department": dept,
                "region": region,
                "item_type": item_type,
                "status": status,
                "urgency": urgency,
                "handler": handler,
                "submit_time": submit_time.strftime("%Y-%m-%d %H:%M:%S"),
                "finish_time": finish_time.strftime("%Y-%m-%d %H:%M:%S") if finish_time else "",
                "duration_hours": duration_hours,
                "satisfaction": satisfaction,
            }
        )
    return pd.DataFrame(rows)


def generate_appeals(n: int = 5000) -> pd.DataFrame:
    """生成群众诉求表。

    Args:
        n (int): 生成的诉求记录总数。

    Returns:
        pd.DataFrame: 群众诉求数据。
    """
    region_names = [r[1] for r in REGIONS]
    category_names = [c[0] for c in APPEAL_CATEGORIES]
    category_keywords = {c[0]: c[1] for c in APPEAL_CATEGORIES}

    rows = []
    for i in range(1, n + 1):
        appeal_id = f"SQ{TODAY.year}{i:06d}"
        region = random.choice(region_names)
        category = random.choice(category_names)
        status = random.choices(APPEAL_STATUSES, weights=[0.55, 0.2, 0.15, 0.1], k=1)[0]

        day_offset = random.choices(range(DAYS_BACK), weights=range(DAYS_BACK, 0, -1), k=1)[0]
        create_time = random_datetime(day_offset)

        # 诉求内容：区域 + 分类关键词拼接
        keyword = random.choice(category_keywords[category].split("、"))
        content = f"{region}居民反映：{keyword}问题，请求核实处理"

        # 已办结有解决时间；已督办标记为超时
        if status == "已办结":
            resolve_time = create_time + timedelta(hours=random.randint(2, 72))
            is_overdue = 0
        elif status == "已督办":
            resolve_time = None
            is_overdue = 1
        else:
            resolve_time = None
            is_overdue = 0

        rows.append(
            {
                "appeal_id": appeal_id,
                "content": content,
                "category": category,
                "region": region,
                "status": status,
                "is_overdue": is_overdue,
                "create_time": create_time.strftime("%Y-%m-%d %H:%M:%S"),
                "resolve_time": resolve_time.strftime("%Y-%m-%d %H:%M:%S") if resolve_time else "",
            }
        )
    return pd.DataFrame(rows)


def generate_inspections(n: int = 600) -> pd.DataFrame:
    """生成综合巡查任务表。

    Args:
        n (int): 生成的巡查任务总数。

    Returns:
        pd.DataFrame: 巡查任务数据。
    """
    region_names = [r[1] for r in REGIONS]

    rows = []
    for i in range(1, n + 1):
        inspection_id = f"XC{TODAY.year}{i:04d}"
        region = random.choice(region_names)
        itype = random.choice(INSPECTION_TYPES)
        status = weighted_choice(INSPECTION_STATUSES, INSPECTION_STATUS_WEIGHTS)
        inspector = random.choice(HANDLERS)

        day_offset = random.choices(range(DAYS_BACK), weights=range(DAYS_BACK, 0, -1), k=1)[0]
        plan_time = random_datetime(day_offset)

        if status == "已完成":
            finish_time = plan_time + timedelta(hours=random.randint(1, 6))
            result = random.choices(["正常", "正常", "正常", "发现问题"], weights=[0.75, 0.75, 0.75, 0.25], k=1)[0]
            remark = "现场情况良好" if result == "正常" else f"发现{itype}方面隐患，已责令整改"
        elif status == "巡查中":
            finish_time = None
            result = "进行中"
            remark = "正在开展现场巡查"
        else:
            finish_time = None
            result = ""
            remark = "待安排巡查"

        rows.append(
            {
                "inspection_id": inspection_id,
                "region": region,
                "inspection_type": itype,
                "status": status,
                "inspector": inspector,
                "plan_time": plan_time.strftime("%Y-%m-%d %H:%M:%S"),
                "finish_time": finish_time.strftime("%Y-%m-%d %H:%M:%S") if finish_time else "",
                "result": result,
                "remark": remark,
            }
        )
    return pd.DataFrame(rows)


def generate_audit_logs(n: int = 3000) -> pd.DataFrame:
    """生成操作审计日志表。

    Args:
        n (int): 生成的日志记录总数。

    Returns:
        pd.DataFrame: 操作审计日志数据。
    """
    rows = []
    for i in range(1, n + 1):
        log_id = f"LOG{TODAY.year}{i:06d}"
        user = random.choice(USERS)
        module = random.choice(MODULES)
        operation = random.choice(OPERATIONS[module])
        level = random.choice(LOG_LEVELS)

        day_offset = random.choices(range(DAYS_BACK), weights=range(DAYS_BACK, 0, -1), k=1)[0]
        op_time = random_datetime(day_offset)

        # 模拟政务内网 IP 段
        ip = f"10.{random.randint(1, 20)}.{random.randint(0, 255)}.{random.randint(1, 254)}"

        rows.append(
            {
                "log_id": log_id,
                "user": user,
                "module": module,
                "operation": operation,
                "level": level,
                "ip_address": ip,
                "op_time": op_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# SQLite 导出
# ---------------------------------------------------------------------------
def export_to_sqlite(tables: dict) -> None:
    """将 6 张数据表同时导出到 SQLite（data/gov_data.db）。

    与 CSV 并存，作为第二种持久化存储形态，便于演示 SQL 查询能力。

    Args:
        tables (dict): 表名 -> DataFrame 的映射。
    """
    import sqlite3

    db_path = DATA_DIR / "gov_data.db"
    conn = sqlite3.connect(db_path)
    try:
        for name, df in tables.items():
            df.to_sql(name, conn, if_exists="replace", index=False)
    finally:
        conn.close()
    print(f"  [OK] {db_path.name:<20} SQLite（{len(tables)} 张表）")


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def main() -> None:
    """一键生成全部 6 张数据表并写出到 data/ 目录。"""
    # 固定随机种子，保证数据可复现
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    # 确保数据目录存在
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  智慧政务大数据平台 - 模拟数据生成")
    print(f"  随机种子：{RANDOM_SEED}  数据周期：近 {DAYS_BACK} 天")
    print("=" * 60)

    # 生成各表
    tables = {
        "departments": generate_departments(),
        "regions": generate_regions(),
        "cases": generate_cases(),
        "appeals": generate_appeals(),
        "inspections": generate_inspections(),
        "audit_logs": generate_audit_logs(),
    }

    # 写出 CSV（UTF-8 带 BOM，保证 Excel 打开中文不乱码）
    for name, df in tables.items():
        path = DATA_DIR / f"{name}.csv"
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"  [OK] {path.name:<20} {len(df):>6} 行")

    # 同时导出 SQLite
    export_to_sqlite(tables)

    print("-" * 60)
    print(f"  全部数据已生成至：{DATA_DIR.resolve()}")
    print("  请运行 `streamlit run app.py` 启动平台")
    print("=" * 60)


if __name__ == "__main__":
    main()
