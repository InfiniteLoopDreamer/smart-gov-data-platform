# 后端 API 服务

基于 **FastAPI** 的政务数据接口，从 SQLite（`data/gov_data.db`）读取真实数据，
复用 `src.metrics` 的分析逻辑，对外提供 REST JSON 接口。

## 快速启动

```bash
# 1. 先生成数据（生成 data/gov_data.db）
cd ..            # 回到项目根目录
python generate_data.py

# 2. 启动后端
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

接口文档：`http://localhost:8000/docs`

## 接口列表

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| POST | `/api/auth/register` | 注册普通用户 | 公开 |
| POST | `/api/auth/login` | 登录，返回令牌 | 公开 |
| GET | `/api/auth/me` | 当前用户信息 | 登录 |
| GET | `/api/users` | 用户列表 | 管理员 |
| GET | `/api/health` | 健康检查 + 表清单 | 公开 |
| GET | `/api/kpi` | 首页核心 KPI（含环比） | 登录 |
| GET | `/api/trend?days=7` | 近 N 天办件趋势 | 登录 |
| GET | `/api/top-items?top=5` | 高频事项 TOP N | 登录 |
| GET | `/api/department-ranking` | 部门效能排名 | 登录 |
| GET | `/api/appeal-categories` | 诉求分类统计 | 登录 |
| GET | `/api/cases?status=&region=` | 办件列表（筛选） | 登录 |
| GET | `/api/logs?level=` | 操作日志（筛选） | 管理员 |
| GET | `/api/sql/status-stats` | SQL 聚合示例：按状态 | 登录 |
| GET | `/api/sql/by-region` | SQL 聚合示例：按区域 | 登录 |

## 认证与角色

- 预置账号：**管理员 `admin / admin123`**、**普通用户 `user / user123`**。
- 密码使用 PBKDF2 加盐哈希存储；登录返回 HMAC 签名令牌（24 小时有效）。
- 调用需登录的接口时，请求头携带：`Authorization: Bearer <token>`。
- 管理员接口（`/api/users`、`/api/logs`）普通用户访问返回 `403`。

## 与前端联动

- **Streamlit 大屏版**：`src/metrics.py` 与后端共用同一套分析逻辑。
- **Vue 后台版**：可用 `axios` 请求上述接口替换 mock 数据，实现「前后端分离」。

## 说明

- 数据源为 `generate_data.py` 生成的 SQLite（`data/gov_data.db`），固定随机种子可复现。
- 已开启 CORS，允许任意来源跨域调用。
