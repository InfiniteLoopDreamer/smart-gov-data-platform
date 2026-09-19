"""
SQLite 数据库访问模块。

generate_data.py 会将 6 张数据表同时导出到 data/gov_data.db，
本模块提供从 SQLite 读取 / 查询的接口，作为 CSV 之外的第二种存储形态，
演示 SQL 查询能力（如按状态统计、按区域聚合等）。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "gov_data.db"
CSV_TABLES = ("cases", "appeals", "departments", "regions", "audit_logs", "inspections")


def ensure_db_from_csv() -> None:
    """若 SQLite 不存在或 cases 为空，则从 data/*.csv 导入（NYC 311 真实数据）。"""
    data_dir = DB_PATH.parent
    need = not DB_PATH.exists()
    if not need:
        conn = sqlite3.connect(DB_PATH)
        try:
            n = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
            need = n == 0
        except sqlite3.Error:
            need = True
        finally:
            conn.close()
    if not need:
        return
    data_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        for name in CSV_TABLES:
            path = data_dir / f"{name}.csv"
            if path.exists():
                pd.read_csv(path).to_sql(name, conn, if_exists="replace", index=False)
    finally:
        conn.close()


def get_connection() -> sqlite3.Connection:
    """建立 SQLite 连接。

    Returns:
        sqlite3.Connection: 数据库连接对象。
    """
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"SQLite 数据库不存在：{DB_PATH.name}，请先运行 `python generate_data.py`。"
        )
    return sqlite3.connect(DB_PATH)


def ensure_indexes() -> None:
    """为常用筛选、排序和时间窗口查询建立幂等索引。"""
    conn = get_connection()
    try:
        existing_tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
        statements = {
            "cases": [
                "CREATE INDEX IF NOT EXISTS idx_cases_submit_time ON cases(submit_time)",
                "CREATE INDEX IF NOT EXISTS idx_cases_status_region ON cases(status, region)",
                "CREATE INDEX IF NOT EXISTS idx_cases_item_type ON cases(item_type)",
            ],
            "appeals": [
                "CREATE INDEX IF NOT EXISTS idx_appeals_create_time ON appeals(create_time)",
                "CREATE INDEX IF NOT EXISTS idx_appeals_status_region ON appeals(status, region)",
            ],
            "audit_logs": [
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_time ON audit_logs(op_time)",
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_level ON audit_logs(level)",
            ],
        }
        for table, sql_list in statements.items():
            if table in existing_tables:
                for sql in sql_list:
                    conn.execute(sql)
        conn.commit()
    finally:
        conn.close()


def list_tables() -> list:
    """列出数据库中的所有表名。"""
    conn = get_connection()
    try:
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()


def read_table(table: str) -> pd.DataFrame:
    """读取整张表为 DataFrame。

    Args:
        table (str): 表名。

    Returns:
        pd.DataFrame: 表数据。
    """
    conn = get_connection()
    try:
        return pd.read_sql_query(f"SELECT * FROM {table}", conn)
    finally:
        conn.close()


def query(sql: str, params: tuple = ()) -> pd.DataFrame:
    """执行任意 SQL 查询并返回 DataFrame（演示用）。

    Args:
        sql (str): SQL 语句（支持参数化）。
        params (tuple): 查询参数。

    Returns:
        pd.DataFrame: 查询结果。
    """
    conn = get_connection()
    try:
        return pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()


def case_status_stats() -> pd.DataFrame:
    """示例：按状态统计办件量（演示 SQL 聚合）。"""
    return query(
        "SELECT status AS 状态, COUNT(*) AS 数量 FROM cases GROUP BY status ORDER BY 数量 DESC"
    )


def case_by_region() -> pd.DataFrame:
    """示例：按区域统计办件量（演示 SQL 聚合 + 排序）。"""
    return query(
        "SELECT region AS 区域, COUNT(*) AS 办件量 FROM cases GROUP BY region ORDER BY 办件量 DESC"
    )
