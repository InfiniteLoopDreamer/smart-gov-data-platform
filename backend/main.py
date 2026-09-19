r"""
智慧政务大数据平台 - 后端 API 服务（FastAPI）。

从 SQLite（data/gov_data.db）读取数据，复用 shared.metrics 的分析逻辑，
对外提供 REST JSON 接口。

运行：
    # 在项目根目录
    .\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload

接口文档：http://127.0.0.1:8001/docs
注意：本机 Hyper-V 常占用 5173/8000 附近端口，默认后端用 8001、前端用 5500。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# 将项目根目录加入 sys.path，复用 src 包（database / metrics）
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from shared import auth, catalog, database, metrics, workflow  # noqa: E402

database.ensure_db_from_csv()

app = FastAPI(title="智慧政务大数据平台 API", version="1.0.0")

# 允许跨域，方便 Vue / Streamlit 前端调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "SMART_GOV_CORS_ORIGINS",
            "http://127.0.0.1:5500,http://localhost:5500",
        ).split(",")
        if origin.strip()
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化用户表并预置管理员/普通用户账号
auth.init_db()
database.ensure_indexes()


# ---------------------------------------------------------------------------
# 认证依赖
# ---------------------------------------------------------------------------
def get_current_user(authorization: str = Header(None)) -> dict:
    """从 Authorization 头解析当前登录用户；无令牌或令牌无效时返回 401。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    try:
        payload = auth.decode_token(authorization[7:])
        current = auth.get_user(payload.get("username", ""))
        if not current or not current.get("active"):
            raise ValueError("账号已停用")
        return {
            "username": current["username"],
            "role": current["role"],
            "name": current["name"],
            "department": current.get("department") or "",
        }
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=f"登录凭证无效：{exc}")


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """仅管理员可访问。"""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


def require_staff_or_admin(user: dict = Depends(get_current_user)) -> dict:
    """部门人员和超级管理员可访问工单中心。"""
    if user.get("role") not in {"staff", "admin"}:
        raise HTTPException(status_code=403, detail="需要部门人员权限")
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


@app.get("/api/kpi", dependencies=[Depends(require_admin)])
def kpi():
    """首页核心 KPI（含环比），复用 metrics.compute_kpis。"""
    return metrics.compute_kpis(_load_cases())


@app.get("/api/trend", dependencies=[Depends(require_admin)])
def trend(days: int = Query(7, ge=1, le=90)):
    """近 N 天办件趋势。"""
    df = metrics.compute_trend(_load_cases(), days=days)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    return df.to_dict(orient="records")


@app.get("/api/top-items", dependencies=[Depends(require_admin)])
def top_items(top: int = Query(5, ge=1, le=20)):
    """高频办理事项 TOP N。"""
    return metrics.compute_top_items(_load_cases(), top=top).to_dict(orient="records")


@app.get("/api/department-ranking", dependencies=[Depends(require_admin)])
def department_ranking():
    """按 6 个业务大类对应的承办部门计算效能排名。"""
    cases_df = _load_cases()
    cases_df["department"] = cases_df["item_type"].map(catalog.department_for_category)
    return metrics.compute_department_ranking(cases_df).to_dict(orient="records")


@app.get("/api/appeal-categories", dependencies=[Depends(require_admin)])
def appeal_categories():
    """诉求分类统计。"""
    return metrics.compute_appeal_category_stats(_load_appeals()).to_dict(orient="records")


@app.get("/api/cases", dependencies=[Depends(require_admin)])
def cases(
    status: str = None,
    region: str = None,
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """办件列表（支持状态 / 区域筛选）。"""
    where = []
    params = []
    if status:
        where.append("status = ?")
        params.append(status)
    if region:
        where.append("region = ?")
        params.append(region)
    where_sql = f" WHERE {' AND '.join(where)}" if where else ""
    sql = f"SELECT * FROM cases{where_sql} ORDER BY submit_time DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    return _to_records(database.query(sql, tuple(params)))


@app.get("/api/logs", dependencies=[Depends(require_admin)])
def logs(level: str = None, limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0)):
    """操作日志列表（支持级别筛选）。"""
    if level:
        df = database.query(
            "SELECT * FROM audit_logs WHERE level = ? ORDER BY op_time DESC LIMIT ? OFFSET ?",
            (level, limit, offset),
        )
    else:
        df = database.query(
            "SELECT * FROM audit_logs ORDER BY op_time DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
    return _to_records(df)


@app.get("/api/sql/status-stats", dependencies=[Depends(require_admin)])
def sql_status_stats():
    """直接 SQL 聚合示例：按状态统计办件量。"""
    return database.case_status_stats().to_dict(orient="records")


@app.get("/api/sql/by-region", dependencies=[Depends(require_admin)])
def sql_by_region():
    """直接 SQL 聚合示例：按区域统计办件量。"""
    return database.case_by_region().to_dict(orient="records")


@app.get("/api/case-categories", dependencies=[Depends(require_admin)])
def case_categories():
    """办件分类占比（饼图/环形图数据源）。"""
    return database.query(
        "SELECT item_type AS name, COUNT(*) AS value FROM cases GROUP BY item_type ORDER BY value DESC"
    ).to_dict(orient="records")


@app.get("/api/region-volume", dependencies=[Depends(get_current_user)])
def region_volume():
    """各区域办件量（柱状图数据源）。"""
    return database.query(
        """SELECT CASE WHEN region = 'Unspecified' THEN '未指定区域' ELSE region END AS name,
                  COUNT(*) AS value
           FROM cases GROUP BY name ORDER BY value DESC"""
    ).to_dict(orient="records")


@app.get("/api/forecast", dependencies=[Depends(require_admin)])
def forecast(days_back: int = Query(28, ge=14, le=90), days_forward: int = Query(7, ge=1, le=30)):
    """办件量 Holt-Winters 预测（含误差评估）。"""
    return metrics.compute_forecast(_load_cases(), days_back=days_back, days_forward=days_forward)


@app.get("/api/anomalies", dependencies=[Depends(require_admin)])
def anomalies(days_back: int = Query(60, ge=14, le=180), threshold: float = Query(3.0, ge=1.0, le=5.0)):
    """办件量异常日期检测（3-sigma）。"""
    return metrics.compute_anomalies(_load_cases(), days_back=days_back, threshold=threshold)


# ---------------------------------------------------------------------------
# 认证接口
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=6, max_length=128)
    name: str = Field(default="", max_length=50)
    department: str = Field(default="", max_length=100)
    role: str = Field(default="user", pattern=r"^(user|staff)$")
    staff_code: str = Field(default="", max_length=100)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=128)


class ManagedUserCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=6, max_length=128)
    name: str = Field(min_length=1, max_length=50)
    role: str = Field(pattern=r"^(admin|staff|user)$")
    department: str = Field(default="", max_length=100)


class ManagedUserUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    role: str = Field(pattern=r"^(admin|staff|user)$")
    department: str = Field(default="", max_length=100)
    active: bool = True


@app.post("/api/auth/register")
def register(req: RegisterRequest):
    """注册群众或部门人员；超级管理员不开放自助注册。"""
    if not req.username or not req.password:
        raise HTTPException(status_code=400, detail="用户名和密码不能为空")
    if req.role == "staff":
        expected_code = os.getenv("SMART_GOV_STAFF_REGISTER_CODE", "demo-staff-2026")
        if not req.staff_code or req.staff_code != expected_code:
            raise HTTPException(status_code=400, detail="部门人员注册码无效")
    try:
        user = auth.register_user(
            req.username, req.password, req.name or req.username, req.department, req.role
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"message": "注册成功", "user": user}


@app.post("/api/auth/login")
def login(req: LoginRequest):
    """登录，返回令牌与用户信息。"""
    user = auth.verify_login(req.username, req.password)
    if user is None:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = auth.create_token(user)
    return {"token": token, "user": user}


@app.get("/api/auth/me")
def me(user: dict = Depends(get_current_user)):
    """当前登录用户信息。"""
    return user


@app.get("/api/users", dependencies=[Depends(require_admin)])
def users_list():
    """用户列表（仅管理员）。"""
    return auth.list_users()


@app.post("/api/users", dependencies=[Depends(require_admin)])
def users_create(req: ManagedUserCreateRequest):
    """管理员创建用户并持久化。"""
    try:
        return auth.create_managed_user(req.username, req.password, req.name, req.role, req.department)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.patch("/api/users/{user_id}", dependencies=[Depends(require_admin)])
def users_update(user_id: int, req: ManagedUserUpdateRequest):
    """管理员修改用户角色、部门或启停状态。"""
    try:
        return auth.update_managed_user(
            user_id, name=req.name, role=req.role, department=req.department, active=req.active
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ---------------------------------------------------------------------------
# 诉求接口（群众端 + 政府端）
# ---------------------------------------------------------------------------
class AppealRequest(BaseModel):
    content: str = Field(min_length=5, max_length=1000)
    category: str = Field(min_length=1, max_length=100)
    region: str = Field(default="未知区域", max_length=100)
    priority: str = Field(default="普通", pattern=r"^(普通|紧急)$")


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
        priority=req.priority,
    )
    return appeal


@app.get("/api/appeals/my", dependencies=[Depends(get_current_user)])
def my_appeals(user: dict = Depends(get_current_user)):
    """当前用户的诉求列表。"""
    return auth.list_appeals_by_user(user["username"])


@app.get("/api/appeals", dependencies=[Depends(require_admin)])
def list_appeals(limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0)):
    """诉求列表（来自 311 真实数据）。"""
    df = database.query(
        "SELECT * FROM appeals ORDER BY create_time DESC LIMIT ? OFFSET ?",
        (limit, offset),
    )
    return _to_records(df)


@app.get("/api/overdue", dependencies=[Depends(require_admin)])
def overdue(days: int = Query(3, ge=1, le=30)):
    """超时工单：在办且超过 N 天未办结的诉求。"""
    cutoff = pd.Timestamp.now().normalize() - pd.Timedelta(days=days)
    return _to_records(
        database.query(
            """SELECT appeal_id, content, category, region, status, create_time
               FROM appeals
               WHERE status != '已办结' AND datetime(create_time) < datetime(?)
               ORDER BY create_time ASC
               LIMIT 100""",
            (cutoff.strftime("%Y-%m-%d %H:%M:%S"),),
        )
    )


# ---------------------------------------------------------------------------
# 数据质量监控接口
# ---------------------------------------------------------------------------
@app.get("/api/quality", dependencies=[Depends(require_admin)])
def data_quality():
    """数据质量监控：从真实数据识别缺失 / 重复 / 异常 / 时间逻辑问题。"""
    return metrics.compute_data_quality(_load_cases(), _load_appeals())


# ---------------------------------------------------------------------------
# 诉求工单处置接口（受理 / 分派 / 办理 / 办结闭环）
# ---------------------------------------------------------------------------
class WorkOrderTransitionRequest(BaseModel):
    action: str = Field(min_length=2, max_length=10)  # 办理 / 办结 / 紧急改派
    department: str | None = Field(default=None, max_length=100)
    handler: str | None = Field(default=None, max_length=50)
    satisfaction: float | None = Field(default=None, ge=1, le=5)
    intervention_note: str | None = Field(default=None, max_length=300)


@app.get("/api/work-orders")
def work_orders(status: str = None, keyword: str = None, limit: int = Query(200, ge=1, le=1000),
                user: dict = Depends(require_staff_or_admin)):
    """部门人员仅看本部门；超级管理员看全局紧急态势。"""
    department = user.get("department") if user.get("role") == "staff" else None
    return workflow.list_work_orders(
        status=status, keyword=keyword, limit=limit, department=department
    )


@app.get("/api/work-orders/summary")
def work_orders_summary(days: int = Query(3, ge=1, le=30),
                        user: dict = Depends(require_staff_or_admin)):
    """诉求工单概览（各状态数量 + 在办 + 超时）。"""
    department = user.get("department") if user.get("role") == "staff" else None
    return workflow.summary(days=days, department=department)


@app.get("/api/work-orders/overdue")
def work_orders_overdue(days: int = Query(3, ge=1, le=30), limit: int = Query(100, ge=1, le=1000),
                        user: dict = Depends(require_staff_or_admin)):
    """超时工单（督办考核用，前端标红）。"""
    department = user.get("department") if user.get("role") == "staff" else None
    return workflow.overdue_work_orders(days=days, limit=limit, department=department)


@app.patch("/api/work-orders/{order_id}")
def update_work_order(order_id: int, req: WorkOrderTransitionRequest,
                      user: dict = Depends(require_staff_or_admin)):
    """执行工单流转动作。"""
    try:
        return workflow.transition(
            order_id,
            req.action,
            department=req.department,
            handler=req.handler,
            satisfaction=req.satisfaction,
            actor_role=user.get("role", ""),
            actor_department=user.get("department", ""),
            intervention_note=req.intervention_note,
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
    """群众端办事指南：20 个原始细分类归并为 6 个业务大类。"""
    grouped = database.query(
        "SELECT item_type, COUNT(*) AS count FROM cases GROUP BY item_type"
    )
    if grouped.empty:
        return []
    totals = {item["name"]: 0 for item in catalog.BUSINESS_CATEGORIES}
    for _, row in grouped.iterrows():
        name = catalog.business_category(str(row["item_type"] or ""))
        totals[name] += int(row["count"])
    items = []
    for item in catalog.BUSINESS_CATEGORIES:
        name, dept = item["name"], item["department"]
        items.append(
            {
                "title": name,
                "category": name,
                "department": dept,
                "count": totals[name],
                "limit": "按 311 工单时限办理",
                "condition": f"属于「{name}」类市民诉求，由 {dept} 受理。",
                "materials": ["身份证明或联系方式", "事发地点与时间说明", "相关现场照片（如有）"],
                "process": ["提交诉求", "系统自动分派", "部门核查办理", "办结反馈"],
            }
        )
    return items


@app.get("/api/service-categories", dependencies=[Depends(get_current_user)])
def service_categories():
    """注册群众和部门人员共用的业务分类/承办部门选项。"""
    return catalog.BUSINESS_CATEGORIES


# ---------------------------------------------------------------------------
# Dashboard 首页综合数据接口（NYC 311 CSV 真实聚合）
# ---------------------------------------------------------------------------
@app.get("/api/dashboard/stats", dependencies=[Depends(require_admin)])
def dashboard_stats():
    """首页统计：直接聚合 NYC 311 CSV 导入后的真实办件/诉求。"""
    cases_df = _load_cases()
    total_cases = len(cases_df)
    total_services = int(cases_df["item_type"].nunique()) if total_cases else 0

    end = cases_df["submit_time"].max() if total_cases else pd.Timestamp.now()
    recent_start = end - pd.Timedelta(days=6)
    previous_start = end - pd.Timedelta(days=13)
    recent = cases_df[cases_df["submit_time"] >= recent_start]
    previous = cases_df[
        (cases_df["submit_time"] >= previous_start)
        & (cases_df["submit_time"] < recent_start)
    ]
    def _pct(a, b):
        if b == 0:
            return 0.0
        return round((a - b) / b * 100, 1)

    def _rate(frame):
        return float((frame["status"] == "已办结").mean() * 100) if len(frame) else 0.0

    completion_rate = _rate(cases_df)
    recent_completion = _rate(recent)
    previous_completion = _rate(previous)
    last_7_start = end - pd.Timedelta(days=6)
    prev_7_start = end - pd.Timedelta(days=13)
    recent_duration = cases_df[
        (cases_df["submit_time"] >= last_7_start) & cases_df["duration_hours"].notna()
    ]["duration_hours"]
    previous_duration = cases_df[
        (cases_df["submit_time"] >= prev_7_start)
        & (cases_df["submit_time"] < last_7_start)
        & cases_df["duration_hours"].notna()
    ]["duration_hours"]
    avg_duration = float(recent_duration.mean()) if len(recent_duration) else 0.0
    avg_duration_prev = float(previous_duration.mean()) if len(previous_duration) else avg_duration
    unfinished_count = int((cases_df["status"] != "已办结").sum()) if total_cases else 0

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
    type_sum = total_cases or 1
    type_distribution = [
        {"name": str(name), "value": int(count), "percent": round(count / type_sum * 100, 1)}
        for name, count in type_counts.items()
    ]
    other_count = total_cases - int(type_counts.sum())
    if other_count > 0:
        type_distribution.append(
            {"name": "其他", "value": other_count, "percent": round(other_count / type_sum * 100, 1)}
        )

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
            {"label": "累计办件量", "value": total_cases, "trend": _pct(len(recent), len(previous)), "trendLabel": "近7日环比", "trendUnit": "%", "color": "#E57373"},
            {"label": "整体办结率", "value": round(completion_rate, 2), "unit": "%", "trend": round(recent_completion - previous_completion, 1), "trendLabel": "较前7日", "trendUnit": "个百分点", "color": "#10B981"},
            {"label": "近7日平均办理时长", "value": round(avg_duration, 1), "unit": "小时", "trend": round(avg_duration_prev - avg_duration, 1), "trendLabel": "效率变化", "trendUnit": "小时", "color": "#F59E0B"},
            {"label": "当前未办结工单", "value": unfinished_count, "trend": None, "trendLabel": "需持续关注", "trendUnit": "", "color": "#EF4444"},
        ],
        "regionData": region_stats,
        "hotServices": hot_services,
        "typeDistribution": type_distribution,
        "deptUsage": dept_stats,
        "notices": notices,
        "overdueCount": unfinished_count,
        "systemStatus": [
            {"name": "数据记录", "status": f"{total_cases:,} 条"},
            {"name": "事项类型", "status": f"{total_services} 类"},
            {"name": "数据截止", "status": end.strftime("%Y-%m-%d") if pd.notna(end) else "-"},
            {"name": "SQLite", "status": "可用" if db_ok else "异常"},
        ],
        "trendSeries": {
            "7": _build_trend(cases_df, 7),
            "30": _build_trend(cases_df, 30),
            "365": _build_trend(cases_df, 365),
        },
        "total": total_cases,
        "dataAsOf": end.strftime("%Y-%m-%d") if pd.notna(end) else None,
    }
