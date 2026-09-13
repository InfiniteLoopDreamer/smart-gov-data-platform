"""
智慧政务大数据平台 - 后端 API 服务（FastAPI）。

从 SQLite（data/gov_data.db）读取真实数据，复用 src.metrics 的分析逻辑，
对外提供 REST JSON 接口。

运行：
    # 在项目根目录
    .\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload

接口文档：http://127.0.0.1:8001/docs
注意：本机 Hyper-V 常占用 5173/8000 附近端口，默认后端用 8001、前端用 5500。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 将项目根目录加入 sys.path，复用 src 包（database / metrics）
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from shared import auth, database, metrics, workflow  # noqa: E402

database.ensure_db_from_csv()

app = FastAPI(title="智慧政务大数据平台 API", version="1.0.0")

# 允许跨域，方便 Vue / Streamlit 前端调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化用户表并预置管理员/普通用户账号
auth.init_db()


# ---------------------------------------------------------------------------
# 认证依赖
# ---------------------------------------------------------------------------
def get_current_user(authorization: str = Header(None)) -> dict:
    """从 Authorization 头解析当前登录用户；无令牌或令牌无效时返回 401。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    try:
        return auth.decode_token(authorization[7:])
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=f"登录凭证无效：{exc}")


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """仅管理员可访问。"""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


# ---------------------------------------------------------------------------
# 数据加载
# ---------------------------------------------------------------------------
def _load_cases() -> pd.DataFrame:
    """从 SQLite 读取办件表并解析时间列。"""
    df = database.read_table("cases")
    df["submit_time"] = pd.to_datetime(df["submit_time"], errors="coerce")
    df["finish_time"] = pd.to_datetime(df["finish_time"], errors="coerce")
    return df


def _load_appeals() -> pd.DataFrame:
    """从 SQLite 读取诉求表并解析时间列。"""
    df = database.read_table("appeals")
    df["create_time"] = pd.to_datetime(df["create_time"], errors="coerce")
    df["resolve_time"] = pd.to_datetime(df["resolve_time"], errors="coerce")
    return df


def _fmt(v):
    """将时间对象格式化为字符串，NaT 转为 None（保证 JSON 可序列化）。"""
    return v.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(v) else None


def _to_records(df: pd.DataFrame) -> list:
    """DataFrame -> JSON 记录列表；时间列转字符串，NaN/NaT 统一转 null。"""
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            out[col] = out[col].apply(_fmt)
    # 用 to_json 统一处理 NaN/NaT -> null，再解析回 Python 对象
    return json.loads(out.to_json(orient="records", force_ascii=False))


# ---------------------------------------------------------------------------
# 接口
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    return {"name": "智慧政务大数据平台 API", "docs": "/docs", "version": "1.0.0"}


@app.get("/api/health")
def health():
    if not database.DB_PATH.exists():
        return {"status": "error", "message": "数据库不存在，请先运行 python generate_data.py"}
    return {"status": "ok", "tables": database.list_tables()}


@app.get("/api/kpi", dependencies=[Depends(get_current_user)])
def kpi():
    """首页核心 KPI（含环比），复用 metrics.compute_kpis。"""
    return metrics.compute_kpis(_load_cases())


@app.get("/api/trend", dependencies=[Depends(get_current_user)])
def trend(days: int = Query(7, ge=1, le=90)):
    """近 N 天办件趋势。"""
    df = metrics.compute_trend(_load_cases(), days=days)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    return df.to_dict(orient="records")


@app.get("/api/top-items", dependencies=[Depends(get_current_user)])
def top_items(top: int = Query(5, ge=1, le=20)):
    """高频办理事项 TOP N。"""
    return metrics.compute_top_items(_load_cases(), top=top).to_dict(orient="records")


@app.get("/api/department-ranking", dependencies=[Depends(get_current_user)])
def department_ranking():
    """部门效能排名。"""
    return metrics.compute_department_ranking(_load_cases()).to_dict(orient="records")


@app.get("/api/appeal-categories", dependencies=[Depends(get_current_user)])
def appeal_categories():
    """诉求分类统计。"""
    return metrics.compute_appeal_category_stats(_load_appeals()).to_dict(orient="records")


@app.get("/api/cases", dependencies=[Depends(get_current_user)])
def cases(status: str = None, region: str = None, limit: int = Query(20, ge=1, le=200)):
    """办件列表（支持状态 / 区域筛选）。"""
    df = _load_cases()
    if status:
        df = df[df["status"] == status]
    if region:
        df = df[df["region"] == region]
    return _to_records(df.head(limit))


@app.get("/api/logs", dependencies=[Depends(require_admin)])
def logs(level: str = None, limit: int = Query(50, ge=1, le=500)):
    """操作日志列表（支持级别筛选）。"""
    df = database.read_table("audit_logs")
    if level:
        df = df[df["level"] == level]
    return _to_records(df.head(limit))


@app.get("/api/sql/status-stats", dependencies=[Depends(get_current_user)])
def sql_status_stats():
    """直接 SQL 聚合示例：按状态统计办件量。"""
    return database.case_status_stats().to_dict(orient="records")


@app.get("/api/sql/by-region", dependencies=[Depends(get_current_user)])
def sql_by_region():
    """直接 SQL 聚合示例：按区域统计办件量。"""
    return database.case_by_region().to_dict(orient="records")


@app.get("/api/case-categories", dependencies=[Depends(get_current_user)])
def case_categories():
    """办件分类占比（饼图/环形图数据源）。"""
    return database.query(
        "SELECT item_type AS name, COUNT(*) AS value FROM cases GROUP BY item_type ORDER BY value DESC"
    ).to_dict(orient="records")


@app.get("/api/region-volume", dependencies=[Depends(get_current_user)])
def region_volume():
    """各区域办件量（柱状图数据源）。"""
    return database.query(
        "SELECT region AS name, COUNT(*) AS value FROM cases GROUP BY region ORDER BY value DESC"
    ).to_dict(orient="records")


@app.get("/api/forecast", dependencies=[Depends(get_current_user)])
def forecast(days_back: int = Query(28, ge=14, le=90), days_forward: int = Query(7, ge=1, le=30)):
    """办件量 Holt-Winters 预测（含误差评估）。"""
    return metrics.compute_forecast(_load_cases(), days_back=days_back, days_forward=days_forward)


@app.get("/api/anomalies", dependencies=[Depends(get_current_user)])
def anomalies(days_back: int = Query(60, ge=14, le=180), threshold: float = Query(3.0, ge=1.0, le=5.0)):
    """办件量异常日期检测（3-sigma）。"""
    return metrics.compute_anomalies(_load_cases(), days_back=days_back, threshold=threshold)


# ---------------------------------------------------------------------------
# 认证接口
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    username: str
    password: str
    name: str = ""
    department: str = ""


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/api/auth/register")
def register(req: RegisterRequest):
    """注册普通用户。"""
    if not req.username or not req.password:
        raise HTTPException(status_code=400, detail="用户名和密码不能为空")
    try:
        user = auth.register_user(req.username, req.password, req.name or req.username, req.department)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"message": "注册成功", "user": user}


@app.post("/api/auth/login")
def login(req: LoginRequest):
    """登录，返回令牌与用户信息。"""
    user = auth.verify_login(req.username, req.password)
    if user is None:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = auth.create_token({"username": user["username"], "role": user["role"]})
    return {"token": token, "user": user}


@app.get("/api/auth/me")
def me(user: dict = Depends(get_current_user)):
    """当前登录用户信息。"""
    return user


@app.get("/api/users", dependencies=[Depends(require_admin)])
def users_list():
    """用户列表（仅管理员）。"""
    return auth.list_users()


# ---------------------------------------------------------------------------
# 诉求接口（群众端 + 政府端）
# ---------------------------------------------------------------------------
class AppealRequest(BaseModel):
    content: str
    category: str
    region: str


@app.post("/api/appeals", dependencies=[Depends(get_current_user)])
def submit_appeal(req: AppealRequest, user: dict = Depends(get_current_user)):
    """群众提交诉求。"""
    if not req.content or not req.category:
        raise HTTPException(status_code=400, detail="诉求内容和分类不能为空")
    appeal = auth.submit_appeal(user["username"], req.content, req.category, req.region or "未知区域")
    # 同步写入工单表，进入政府端「诉求工单处置」闭环
    workflow.create_work_order(
        source="citizen",
        source_id=appeal["id"],
        appeal_id=f"SQ{appeal['id']:06d}",
        content=req.content,
        category=req.category,
        region=req.region or "未知区域",
    )
    return appeal


@app.get("/api/appeals/my", dependencies=[Depends(get_current_user)])
def my_appeals(user: dict = Depends(get_current_user)):
    """当前用户的诉求列表。"""
    return auth.list_appeals_by_user(user["username"])


@app.get("/api/appeals", dependencies=[Depends(get_current_user)])
def list_appeals(limit: int = Query(50, ge=1, le=500)):
    """诉求列表（来自 311 真实数据）。"""
    return _to_records(_load_appeals().head(limit))


@app.get("/api/overdue", dependencies=[Depends(get_current_user)])
def overdue(days: int = Query(3, ge=1, le=30)):
    """超时工单：在办且超过 N 天未办结的诉求。"""
    appeals = _load_appeals()
    cutoff = pd.Timestamp.now().normalize() - pd.Timedelta(days=days)
    overdue = appeals[
        (appeals["status"] != "已办结") & (appeals["create_time"] < cutoff)
    ]
    cols = ["appeal_id", "content", "category", "region", "status", "create_time"]
    return _to_records(overdue[cols].head(100))


# ---------------------------------------------------------------------------
# 数据质量监控接口
# ---------------------------------------------------------------------------
@app.get("/api/quality", dependencies=[Depends(get_current_user)])
def data_quality():
    """数据质量监控：从真实数据识别缺失 / 重复 / 异常 / 时间逻辑问题。"""
    return metrics.compute_data_quality(_load_cases(), _load_appeals())


# ---------------------------------------------------------------------------
# 诉求工单处置接口（受理 / 分派 / 办理 / 办结闭环）
# ---------------------------------------------------------------------------
class WorkOrderTransitionRequest(BaseModel):
    action: str  # 受理 / 分派 / 办理 / 办结
    department: str = None
    handler: str = None
    satisfaction: float = None


@app.get("/api/work-orders", dependencies=[Depends(require_admin)])
def work_orders(status: str = None, keyword: str = None, limit: int = Query(200, ge=1, le=1000)):
    """诉求工单列表（仅管理员）。"""
    return workflow.list_work_orders(status=status, keyword=keyword, limit=limit)


@app.get("/api/work-orders/summary", dependencies=[Depends(require_admin)])
def work_orders_summary(days: int = Query(3, ge=1, le=30)):
    """诉求工单概览（各状态数量 + 在办 + 超时）。"""
    return workflow.summary(days=days)


@app.get("/api/work-orders/overdue", dependencies=[Depends(require_admin)])
def work_orders_overdue(days: int = Query(3, ge=1, le=30), limit: int = Query(100, ge=1, le=1000)):
    """超时工单（督办考核用，前端标红）。"""
    return workflow.overdue_work_orders(days=days, limit=limit)


@app.patch("/api/work-orders/{order_id}", dependencies=[Depends(require_admin)])
def update_work_order(order_id: int, req: WorkOrderTransitionRequest):
    """执行工单流转动作。"""
    try:
        return workflow.transition(
            order_id,
            req.action,
            department=req.department,
            handler=req.handler,
            satisfaction=req.satisfaction,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


def _short_dept(name: str) -> str:
    mapping = {
        "New York City Police Department": "市警察局",
        "Department of Transportation": "交通局",
        "Department of Housing Preservation and Development": "住房局",
        "Department of Environmental Protection": "环保局",
        "Department of Sanitation": "环卫局",
        "Department of Health and Mental Hygiene": "卫生局",
        "Department of Buildings": "建筑局",
        "Department of Parks and Recreation": "公园局",
        "311 Customer Service Center": "311 热线中心",
    }
    return mapping.get(name, name)


def _build_trend(cases_df: pd.DataFrame, days: int) -> dict:
    if cases_df.empty or cases_df["submit_time"].isna().all():
        return {"x": [], "y": []}
    end = cases_df["submit_time"].max()
    start = end - pd.Timedelta(days=int(days))
    sub = cases_df[cases_df["submit_time"] >= start]
    if sub.empty:
        sub = cases_df
    if days >= 180:
        grouped = sub.groupby(sub["submit_time"].dt.to_period("M")).size()
        x = [p.strftime("%Y-%m") for p in grouped.index]
        y = [int(v) for v in grouped.values]
    else:
        grouped = sub.groupby(sub["submit_time"].dt.strftime("%m-%d")).size()
        x = list(grouped.index)
        y = [int(v) for v in grouped.values]
        if len(x) > 14:
            step = max(1, len(x) // 12)
            x, y = x[::step], y[::step]
    return {"x": x, "y": y}


@app.get("/api/service-guides", dependencies=[Depends(get_current_user)])
def service_guides():
    """办事指南：由真实办件事项与部门聚合。"""
    df = _load_cases()
    if df.empty:
        return []
    grouped = (
        df.groupby(["item_type", "department"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .head(40)
    )
    items = []
    for _, row in grouped.iterrows():
        name = str(row["item_type"] or "未分类事项")
        dept = _short_dept(str(row["department"] or "承办部门"))
        items.append(
            {
                "title": name,
                "category": name,
                "department": dept,
                "count": int(row["count"]),
                "limit": "按 311 工单时限办理",
                "condition": f"属于「{name}」类市民诉求，由 {dept} 受理。",
                "materials": ["身份证明或联系方式", "事发地点与时间说明", "相关现场照片（如有）"],
                "process": ["提交诉求", "部门分派", "现场核查/办理", "办结反馈"],
            }
        )
    return items


# ---------------------------------------------------------------------------
# Dashboard 首页综合数据接口（NYC 311 CSV 真实聚合）
# ---------------------------------------------------------------------------
@app.get("/api/dashboard/stats", dependencies=[Depends(get_current_user)])
def dashboard_stats():
    """首页统计：直接聚合 NYC 311 CSV 导入后的真实办件/诉求。"""
    cases_df = _load_cases()
    total_cases = len(cases_df)
    total_services = int(cases_df["item_type"].nunique()) if total_cases else 0
    try:
        total_users = len(database.read_table("users"))
    except Exception:
        total_users = 2

    end = cases_df["submit_time"].max() if total_cases else pd.Timestamp.now()
    prev_start = end - pd.Timedelta(days=60)
    mid = end - pd.Timedelta(days=30)
    recent = cases_df[cases_df["submit_time"] >= mid]
    previous = cases_df[(cases_df["submit_time"] >= prev_start) & (cases_df["submit_time"] < mid)]
    def _pct(a, b):
        if b == 0:
            return 0.0
        return round((a - b) / b * 100, 1)

    region_stats = database.query(
        "SELECT region AS name, COUNT(*) AS value FROM cases GROUP BY region ORDER BY value DESC"
    ).to_dict(orient="records")
    region_stats = [r for r in region_stats if r.get("name") and r["name"] != "Unspecified"]

    hot_raw = database.query(
        "SELECT item_type AS name, COUNT(*) AS value FROM cases GROUP BY item_type ORDER BY value DESC LIMIT 5"
    ).to_dict(orient="records")
    hot_services = [{"name": s["name"], "count": s["value"]} for s in hot_raw]

    dept_raw = database.query(
        "SELECT department AS name, COUNT(*) AS value FROM cases GROUP BY department ORDER BY value DESC LIMIT 8"
    ).to_dict(orient="records")
    dept_stats = [{"name": _short_dept(d["name"]), "value": d["value"]} for d in dept_raw]

    type_counts = cases_df["item_type"].value_counts().head(5)
    type_sum = int(type_counts.sum()) or 1
    type_distribution = [
        {"name": str(name), "value": int(count), "percent": round(count / type_sum * 100, 1)}
        for name, count in type_counts.items()
    ]

    notices = []
    try:
        logs = database.read_table("audit_logs")
        if not logs.empty:
            logs = logs.sort_values("op_time", ascending=False).head(5)
            for _, row in logs.iterrows():
                t = str(row.get("op_time") or "")
                notices.append({
                    "title": f"{row.get('module', '')}：{row.get('operation', '')}",
                    "time": t[5:10] if len(t) >= 10 else t,
                })
    except Exception:
        notices = []

    db_ok = database.DB_PATH.exists()
    return {
        "stats": [
            {"label": "政务数据总量", "value": total_cases, "trend": _pct(len(recent), len(previous)), "color": "#E57373"},
            {"label": "服务事项总数", "value": total_services, "trend": 0, "color": "#FFB74D"},
            {"label": "办件总量", "value": total_cases, "trend": _pct(len(recent), len(previous)), "color": "#FFD54F"},
            {"label": "用户总数", "value": total_users, "trend": 0, "color": "#FFCC80"},
        ],
        "regionData": region_stats,
        "hotServices": hot_services,
        "typeDistribution": type_distribution,
        "deptUsage": dept_stats,
        "notices": notices,
        "overdueCount": int((cases_df["status"] != "已办结").sum()) if total_cases else 0,
        "systemStatus": [
            {"name": "数据采集服务", "status": "正常" if total_cases else "异常"},
            {"name": "数据处理服务", "status": "正常"},
            {"name": "应用服务", "status": "正常"},
            {"name": "数据库服务", "status": "正常" if db_ok else "异常"},
            {"name": "网络服务", "status": "正常"},
        ],
        "trendSeries": {
            "7": _build_trend(cases_df, 7),
            "30": _build_trend(cases_df, 30),
            "365": _build_trend(cases_df, 365),
        },
        "total": total_cases,
    }