# 数据大屏（Streamlit）

基于 Streamlit + Pandas + ECharts 的政务数据可视化大屏，深色科技风，共 7 大模块、17 个功能点。

## 快速启动

```bash
# 1. 生成数据（项目根目录）
cd ..
python generate_data.py

# 2. 可选：下载 ECharts 到本地（断网也能渲染图表）
python download_echarts.py

# 3. 启动
cd dashboard
pip install -r requirements.txt
streamlit run app.py
```

## 功能清单

- **首页 · 一屏统览**：4 KPI 指标卡（含环比）、办件趋势、诉求热力、高频事项 TOP5、待办中心、核心发现
- **业务办理 · 一网通办**：办件管理、审批服务（持久化）、一件事导办
- **城市治理 · 一网统管**：城市一张图、综合巡查、联动指挥
- **数据资源 · 一网共享**：数据资产、资源目录、数据服务
- **监督调度**：社情民意、督办流水、考核评价
- **安全与决策**：安全审计、领导看板、趋势预测
- **系统管理**：系统设置

## 目录结构

```
dashboard/
├── app.py                # 主入口（首页）
├── src/                  # 大屏专用：charts/data_loader/sidebar/utils
├── pages/                # 6 个业务页
├── assets/               # style.css + echarts.min.js
├── .streamlit/           # 主题配置
├── download_echarts.py   # ECharts 离线下载脚本
└── requirements.txt
```

> 共享逻辑（指标计算 `metrics`、SQLite 访问 `database`、认证 `auth`、状态持久化 `state`）位于项目根目录的 `shared/`，与后端共用。

## 数据来源

`../generate_data.py` 生成的 `data/*.csv`（含 6 张相互关联的模拟表，固定随机种子可复现）。
