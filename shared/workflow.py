"""
诉求工单处置模块：群众诉求 → 受理 → 分派 → 部门办理 → 办结 的闭环流程。

工单来源（真实数据）：
- 311 热线诉求：data/gov_data.db 的 appeals 表中尚未办结的真实工单；
- 群众在线提交：citizen_appeals 表中的诉求（群众端「我要反映」）。

状态机：
    待受理 --受理--> 已受理 --分派--> 已分派 --办理--> 办理中 --办结--> 已办结

管理员在政府端「诉求工单处置」页面对工单进行流转；群众提交的诉求在流转时
同步回写 citizen_appeals.status，群众端即可看到进度。
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "gov_data.db"

# 工单流转顺序（index 越小越靠前）
STATUS_FLOW = ["待受理", "已受理", "已分派", "办理中", "已办结"]
OPEN_STATUSES = ["待受理", "已受理", "已分派", "办理中"]

# 流转动作 -> 下一状态
ACTION_TO_STATUS = {
    "受理": "已受理",
    "分派": "已分派",
    "办理": "办理中",
    "办结": "已办结",
}

# 分派时可选的部门与办理人（演示字典；真实系统来自部门/人员主数据）
DEPARTMENTS = [
    "市城市管理局",
    "市交通运输局",
    "市生态环境局",
    "市住房和城乡建设局",
    "市市场监督管理局",
    "市公安局",
    "市教育局",
    "市卫生健康委员会",
]
HANDLERS = ["张伟", "李娜", "王强", "刘洋", "陈静", "赵磊", "孙敏", "周涛"]

# 群众端可见的状态（比政府端更粗粒度）
_CITIZEN_STATUS_MAP = {
    "待受理": "已受理",
    "已受理": "已受理",
    "已分派": "已受理",
    "办理中": "办理中",
    "已办结": "已办结",
}


def get_conn() -> sqlite3.Connection:
    """建立 SQLite 连接（返回 Row 便于按列名访问）。"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def init_work_orders() -> None:
    """建 work_orders 表，并在首次运行时用真实诉求（appeals + citizen_appeals）播种。"""
    conn = get_conn()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS work_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                appeal_id TEXT,
                content TEXT NOT NULL,
                category TEXT NOT NULL,
                region TEXT NOT NULL,
                department TEXT,
                handler TEXT,
                status TEXT NOT NULL DEFAULT '待受理',
                satisfaction REAL,
                source TEXT NOT NULL DEFAULT '311',
                source_id INTEGER,
                create_time TEXT NOT NULL,
                update_time TEXT,
                finish_time TEXT
            )
            """
        )
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM work_orders").fetchone()[0]
        if count == 0:
            _seed(conn)
    finally:
        conn.close()


def _seed(conn: sqlite3.Connection) -> None:
    """将未办结的真实诉求写入工单表，形成初始待办池。"""
    rows = []

    # 1) 311 真实诉求：在办（未办结）工单，按索引确定性分布到不同流转阶段
    appeals = conn.execute(
        "SELECT appeal_id, content, category, region, status, create_time "
        "FROM appeals WHERE status != '已办结' ORDER BY create_time DESC"
    ).fetchall()
    for i, a in enumerate(appeals):
        status = STATUS_FLOW[i % 4]  # 待受理/已受理/已分派/办理中 循环
        dept = DEPARTMENTS[i % len(DEPARTMENTS)]
        handler = HANDLERS[i % len(HANDLERS)]
        rows.append(
            {
                "appeal_id": a["appeal_id"],
                "content": a["content"],
                "category": a["category"],
                "region": a["region"],
                "department": dept if status in ("已分派", "办理中") else None,
                "handler": handler if status in ("已分派", "办理中") else None,
                "status": status,
                "source": "311",
                "source_id": None,
                "create_time": a["create_time"],
            }
        )

    # 2) 群众已在线提交、但尚未进入闭环的诉求
    citizen = conn.execute(
        "SELECT id, content, category, region, status, create_time FROM citizen_appeals"
    ).fetchall()
    for c in citizen:
        rows.append(
            {
                "appeal_id": f"SQ{c['id']:06d}",
                "content": c["content"],
                "category": c["category"],
                "region": c["region"],
                "department": None,
                "handler": None,
                "status": "待受理",
                "source": "citizen",
                "source_id": c["id"],
                "create_time": c["create_time"],
            }
        )

    now = _now()
    for r in rows:
        conn.execute(
            """
            INSERT INTO work_orders
                (appeal_id, content, category, region, department, handler, status,
                 source, source_id, create_time, update_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                r["appeal_id"],
                r["content"],
                r["category"],
                r["region"],
                r["department"],
                r["handler"],
                r["status"],
                r["source"],
                r["source_id"],
                r["create_time"],
                now,
            ),
        )
    conn.commit()


def create_work_order(source: str, source_id: int | None, appeal_id: str,
                      content: str, category: str, region: str) -> dict:
    """新增一条工单（群众提交诉求时调用）。"""
    init_work_orders()
    now = _now()
    conn = get_conn()
    try:
        cur = conn.execute(
            """
            INSERT INTO work_orders
                (appeal_id, content, category, region, status, source, source_id,
                 create_time, update_time)
            VALUES (?, ?, ?, ?, '待受理', ?, ?, ?, ?)
            """,
            (appeal_id, content, category, region, source, source_id, now, now),
        )
        conn.commit()
        order_id = cur.lastrowid
        return _get_order(conn, order_id)
    finally:
        conn.close()


def list_work_orders(status: str = None, keyword: str = None, limit: int = 100) -> list:
    """工单列表（支持状态/关键词筛选），在办优先、时间倒序。"""
    init_work_orders()
    conn = get_conn()
    try:
        where, params = [], []
        if status:
            where.append("status = ?")
            params.append(status)
        if keyword:
            where.append("(content LIKE ? OR appeal_id LIKE ? OR region LIKE ?)")
            like = f"%{keyword}%"
            params.extend([like, like, like])
        where_sql = (" WHERE " + " AND ".join(where)) if where else ""
        # 用 CASE 表达式按流转顺序排序（待受理排最前）
        status_order = "CASE status " + " ".join(
            f"WHEN '{s}' THEN {i}" for i, s in enumerate(STATUS_FLOW)
        ) + " END"
        sql = (
            f"SELECT * FROM work_orders{where_sql} "
            f"ORDER BY {status_order}, create_time DESC LIMIT ?"
        )
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def summary(days: int = 3) -> dict:
    """工单概览：各状态数量 + 在办 + 超时（超过 N 天未办结）。"""
    init_work_orders()
    conn = get_conn()
    try:
        status_counts = {
            r["status"]: r["c"]
            for r in conn.execute("SELECT status, COUNT(*) AS c FROM work_orders GROUP BY status").fetchall()
        }
        total = sum(status_counts.values())
        open_count = sum(status_counts.get(s, 0) for s in OPEN_STATUSES)

        cutoff = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - days * 86400))
        overdue = conn.execute(
            "SELECT COUNT(*) FROM work_orders WHERE status IN (?, ?, ?, ?) AND create_time < ?",
            (*OPEN_STATUSES, cutoff),
        ).fetchone()[0]

        return {
            "total": total,
            "open": open_count,
            "overdue": overdue,
            "finished": status_counts.get("已办结", 0),
            "status_counts": [
                {"status": s, "count": status_counts.get(s, 0)} for s in STATUS_FLOW
            ],
        }
    finally:
        conn.close()


def overdue_work_orders(days: int = 3, limit: int = 100) -> list:
    """超时工单：在办且超过 N 天未办结（用于督办考核标红）。"""
    init_work_orders()
    conn = get_conn()
    try:
        cutoff = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - days * 86400))
        rows = conn.execute(
            "SELECT * FROM work_orders WHERE status IN (?, ?, ?, ?) AND create_time < ? "
            "ORDER BY create_time ASC LIMIT ?",
            (*OPEN_STATUSES, cutoff, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def transition(order_id: int, action: str, department: str = None,
               handler: str = None, satisfaction: float = None) -> dict:
    """执行一次流转动作（受理/分派/办理/办结），返回更新后的工单。"""
    init_work_orders()
    conn = get_conn()
    try:
        order = _get_order(conn, order_id)
        if order is None:
            raise ValueError("工单不存在")
        if order["status"] == "已办结":
            raise ValueError("工单已办结，无法继续流转")

        expected = {
            "受理": "待受理",
            "分派": "已受理",
            "办理": "已分派",
            "办结": "办理中",
        }
        if expected.get(action) != order["status"]:
            raise ValueError(f"当前状态「{order['status']}」不能执行「{action}」")

        next_status = ACTION_TO_STATUS[action]
        now = _now()
        if action == "分派":
            if not department:
                raise ValueError("分派需选择办理部门")
            conn.execute(
                "UPDATE work_orders SET status=?, department=?, handler=?, update_time=? WHERE id=?",
                (next_status, department, handler, now, order_id),
            )
        elif action == "办结":
            conn.execute(
                "UPDATE work_orders SET status=?, satisfaction=?, update_time=?, finish_time=? WHERE id=?",
                (next_status, satisfaction, now, now, order_id),
            )
        else:
            conn.execute(
                "UPDATE work_orders SET status=?, update_time=? WHERE id=?",
                (next_status, now, order_id),
            )
        conn.commit()

        # 群众提交的诉求：同步进度与满意度到 citizen_appeals，群众端「我的诉求」可见
        if order["source"] == "citizen" and order["source_id"]:
            conn.execute(
                "UPDATE citizen_appeals SET status=?, satisfaction=? WHERE id=?",
                (_CITIZEN_STATUS_MAP[next_status], satisfaction, order["source_id"]),
            )
            conn.commit()

        return _get_order(conn, order_id)
    finally:
        conn.close()


def _get_order(conn: sqlite3.Connection, order_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM work_orders WHERE id=?", (order_id,)).fetchone()
    return dict(row) if row else None
