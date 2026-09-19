-- 智慧政务数据分析：6 个可复用的业务问题（SQLite）
-- 运行方式：sqlite3 data/gov_data.db < analysis/business_questions.sql

-- Q1 数据范围与核心口径：避免把同源的 appeals / cases 重复计数。
SELECT
    COUNT(*) AS work_order_count,
    COUNT(DISTINCT item_type) AS item_type_count,
    COUNT(DISTINCT region) AS region_count,
    MIN(date(submit_time)) AS start_date,
    MAX(date(submit_time)) AS end_date,
    ROUND(100.0 * SUM(status = '已办结') / COUNT(*), 2) AS completion_rate_pct
FROM cases;

-- Q2 区域集中度：识别重点治理区域及累计贡献。
WITH region_volume AS (
    SELECT region, COUNT(*) AS case_count
    FROM cases
    GROUP BY region
), ranked AS (
    SELECT
        region,
        case_count,
        ROUND(100.0 * case_count / SUM(case_count) OVER (), 2) AS share_pct,
        ROUND(
            100.0 * SUM(case_count) OVER (ORDER BY case_count DESC)
            / SUM(case_count) OVER (),
            2
        ) AS cumulative_share_pct
    FROM region_volume
)
SELECT * FROM ranked ORDER BY case_count DESC;

-- Q3 事项 Pareto：头部事项是否占据大部分工作量。
WITH item_volume AS (
    SELECT item_type, COUNT(*) AS case_count
    FROM cases
    GROUP BY item_type
)
SELECT
    item_type,
    case_count,
    ROUND(100.0 * case_count / SUM(case_count) OVER (), 2) AS share_pct,
    ROUND(
        100.0 * SUM(case_count) OVER (ORDER BY case_count DESC)
        / SUM(case_count) OVER (),
        2
    ) AS cumulative_share_pct
FROM item_volume
ORDER BY case_count DESC;

-- Q4 部门效能：同时观察工作量、办理时长和办结率，避免只按数量排名。
SELECT
    department,
    COUNT(*) AS case_count,
    ROUND(AVG(CASE WHEN status = '已办结' THEN duration_hours END), 2) AS avg_duration_hours,
    ROUND(100.0 * SUM(status = '已办结') / COUNT(*), 2) AS completion_rate_pct,
    ROUND(100.0 * SUM(duration_hours > 24) / COUNT(*), 2) AS over_24h_rate_pct
FROM cases
GROUP BY department
HAVING COUNT(*) >= 20
ORDER BY completion_rate_pct DESC, avg_duration_hours ASC;

-- Q5 每日趋势与 7 日移动平均：支持高峰识别和排班分析。
WITH daily AS (
    SELECT date(submit_time) AS day, COUNT(*) AS case_count
    FROM cases
    GROUP BY date(submit_time)
)
SELECT
    day,
    case_count,
    ROUND(
        AVG(case_count) OVER (
            ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ),
        2
    ) AS moving_avg_7d,
    case_count - LAG(case_count) OVER (ORDER BY day) AS day_over_day_change
FROM daily
ORDER BY day;

-- Q6 异常日归因：按“日期 × 区域 × 事项”查看贡献，解释波动来自哪里。
WITH daily_dimension AS (
    SELECT
        date(submit_time) AS day,
        region,
        item_type,
        COUNT(*) AS case_count
    FROM cases
    GROUP BY date(submit_time), region, item_type
), with_change AS (
    SELECT
        *,
        case_count - LAG(case_count) OVER (
            PARTITION BY region, item_type ORDER BY day
        ) AS change_vs_previous_day
    FROM daily_dimension
)
SELECT *
FROM with_change
WHERE change_vs_previous_day IS NOT NULL
ORDER BY ABS(change_vs_previous_day) DESC
LIMIT 50;
