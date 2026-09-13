# 智慧政务数据管理系统后台

基于 **Vue 3 + Vite + Element Plus + ECharts** 的政务数据管理后台，参照 Cameo 后台脚手架风格（深蓝侧边栏 + 白色顶栏 + 浅灰内容区，主色 `#2B5FD7`）。

## 功能清单

- **登录 / 注册**：真实后端认证（PBKDF2 密码哈希 + 签名令牌）
- **角色权限（RBAC）**：管理员 / 普通用户，菜单、路由、按钮、接口四级权限
- **首页看板**：4 张统计卡 + 办件趋势 + 区域办件量 + 分类占比 + 最近办件
- **办件管理**：查询筛选 + 详情抽屉 + 新增办件 + 真分页
- **数据清洗**：数据概览 + 清洗规则配置
- **统计报表**：状态分布 + 部门效能排名 + 月度趋势
- **用户管理 / 操作日志 / 系统设置**：管理员专属

## 技术栈

| 技术 | 版本 | 用途 |
| --- | --- | --- |
| Vue | 3.4 | 前端框架 |
| Vite | 5 | 构建工具 |
| Element Plus | 2.7 | UI 组件库 |
| Vue Router | 4.3 | 路由 |
| ECharts | 5.5 | 图表 |

## 快速启动

```bash
cd frontend
npm install
npm run dev
```

浏览器自动打开 `http://localhost:5173`。

## 部署

已内置 Vercel / Netlify 配置（`vercel.json` / `netlify.toml`），可直接：

- **Vercel**：导入仓库，框架选 Vite，无需额外配置。
- **Netlify**：`npm run build`，发布目录选 `dist`。

预置账号：管理员 `admin / admin123`，普通用户 `user / user123`。

## 项目结构

```
frontend/
├── index.html
├── package.json
├── vite.config.js
├── vercel.json / netlify.toml
├── public/
│   └── favicon.svg
└── src/
    ├── main.js            # 入口
    ├── App.vue
    ├── api/index.js       # 后端接口客户端（axios）
    ├── auth/index.js      # 认证状态工具
    ├── router/index.js    # 路由（含角色守卫）
    ├── styles/index.scss  # 全局主题
    ├── layout/            # 布局：侧边栏 / 顶栏
    ├── components/        # BaseChart / StatCard
    ├── views/             # 页面（login/dashboard/case/.../system）
    └── mock/data.js       # 兜底演示数据
```

## 说明

本前端通过 axios 调用后端（`../backend`）接口获取真实数据；后端未启动时自动回退到 mock 演示数据。
