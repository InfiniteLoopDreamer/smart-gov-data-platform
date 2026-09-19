# 后端 API 服务

基于 **FastAPI** 的政务数据接口，从 SQLite（`data/gov_data.db`）读取真实数据，
复用 `shared.metrics` 的分析逻辑，对外提供 REST JSON 接口。

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
| GET | `/api/users` | 用户列表（含启停状态） | 管理员 |
| POST | `/api/users` | 创建用户并绑定角色/部门 | 管理员 |
| PATCH | `/api/users/{id}` | 编辑角色、部门与启停状态 | 管理员 |
| GET | `/api/health` | 健康检查 + 表清单 | 公开 |
| GET | `/api/kpi` | 首页核心 KPI（含环比） | 管理员 |
| GET | `/api/trend?days=7` | 近 N 天办件趋势 | 管理员 |
| GET | `/api/top-items?top=5` | 高频事项 TOP N | 管理员 |
| GET | `/api/department-ranking` | 部门效能排名 | 管理员 |
| GET | `/api/appeal-categories` | 诉求分类统计 | 管理员 |
| GET | `/api/cases?status=&region=&limit=&offset=` | 办件列表（筛选/分页） | 管理员 |
| GET | `/api/logs?level=` | 操作日志（筛选） | 管理员 |
| GET | `/api/sql/status-stats` | SQL 聚合示例：按状态 | 管理员 |
| GET | `/api/sql/by-region` | SQL 聚合示例：按区域 | 管理员 |

## 认证与角色

- 预置账号：**超级管理员 `admin / admin123`**、**群众 `user / user123`**、**部门人员 `traffic_staff / staff123`**。
- 密码使用 PBKDF2 加盐哈希存储；登录返回 HMAC 签名令牌（24 小时有效）。
- 部门人员注册必须提供 `SMART_GOV_STAFF_REGISTER_CODE` 配置的单位注册码，且注册时绑定部门；超级管理员不开放自助注册。
- 调用需登录的接口时，请求头携带：`Authorization: Bearer <token>`。
- 群众端将 20 个原始分析细分类归并为 6 个业务大类，并自动分派到对应部门。
- 部门人员只读取和办理所属部门工单；超级管理员不能日常办理，只能对标记为紧急的工单跨部门改派并填写介入原因。

## 与前端联动

- **Streamlit 大屏版**：`src/metrics.py` 与后端共用同一套分析逻辑。
- **Vue 后台版**：可用 `axios` 请求上述接口替换 mock 数据，实现「前后端分离」。

## 说明

- 数据源为 `generate_data.py` 生成的 SQLite（`data/gov_data.db`），固定随机种子可复现。
- CORS 默认只允许本机前端，可通过 `SMART_GOV_CORS_ORIGINS` 配置允许来源。
- 生产环境必须通过 `SMART_GOV_SECRET` 设置独立令牌密钥。
