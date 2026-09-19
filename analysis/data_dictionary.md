# 数据口径与字段来源

| 字段/指标 | 来源 | 口径说明 | 是否用于核心结论 |
| --- | --- | --- | :---: |
| `appeal_id` | NYC 311 `Unique Key` | 工单唯一标识 | 是 |
| `item_type/category` | NYC 311 `Complaint Type` | 经过中文字典映射的事项类型 | 是 |
| `region` | NYC 311 `Borough` | 五大行政区；缺失记为 `Unspecified` | 是 |
| `department` | NYC 311 `Agency Name` | 承办部门 | 是 |
| `submit_time/create_time` | NYC 311 `Created Date` | 工单创建时间 | 是 |
| `finish_time/resolve_time` | NYC 311 `Closed Date` | 工单关闭时间 | 是 |
| `duration_hours` | 派生 | 办结时间减创建时间 | 是 |
| `status` | NYC 311 `Status` | 映射为办理中/已办结等中文状态 | 是 |
| `urgency` | 模拟 | 用于界面展示的随机字段 | 否 |
| `handler` | 模拟 | 用于工单流转演示 | 否 |
| `satisfaction` | 模拟 | 随机生成 3～5 分 | 否 |
| `employee_count` | 模拟 | 部门展示字段 | 否 |
| `population_wan/area_km2` | 模拟 | 区域展示字段 | 否 |

## 统一统计原则

`appeals` 和 `cases` 由同一批 NYC 311 工单一对一映射，分别服务于诉求分析和办件分析。描述数据规模时统一写作“50,000 条工单，映射为诉求/办件主题表”，不得相加为 100,000 条独立样本。
