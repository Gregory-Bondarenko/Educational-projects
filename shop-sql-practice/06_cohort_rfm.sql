-- Часть 4. Когортный анализ и RFM

-- Задание 12. Retention по когортам: % клиентов каждой месячной когорты
-- (по дате регистрации), которые продолжали покупать через 0, 1, 2... месяцев
WITH cohorts AS (
    SELECT customer_id, date_trunc('month', signup_date)::date AS cohort_month
    FROM customers
),
activity AS (
    SELECT DISTINCT o.customer_id, date_trunc('month', o.order_date)::date AS activity_month
    FROM orders o
    WHERE o.status = 'completed'
),
cohort_activity AS (
    SELECT
        c.cohort_month,
        c.customer_id,
        (date_part('year', a.activity_month) - date_part('year', c.cohort_month)) * 12
            + (date_part('month', a.activity_month) - date_part('month', c.cohort_month)) AS month_number
    FROM cohorts c
    JOIN activity a ON a.customer_id = c.customer_id
),
cohort_size AS (
    SELECT cohort_month, COUNT(*) AS num_customers FROM cohorts GROUP BY cohort_month
)
SELECT
    ca.cohort_month,
    ca.month_number,
    cs.num_customers,
    COUNT(DISTINCT ca.customer_id) AS active_customers,
    ROUND(COUNT(DISTINCT ca.customer_id)::numeric / cs.num_customers * 100, 1) AS retention_pct
FROM cohort_activity ca
JOIN cohort_size cs ON cs.cohort_month = ca.cohort_month
WHERE ca.month_number BETWEEN 0 AND 6
GROUP BY ca.cohort_month, ca.month_number, cs.num_customers
ORDER BY ca.cohort_month, ca.month_number;

-- Задание 13. RFM-сегментация клиентов (Recency, Frequency, Monetary)
-- через NTILE на 5 групп по каждому признаку;
-- давность считаем от 1 января 2025, то есть сразу после конца данных
WITH order_totals AS (
    SELECT o.order_id, o.customer_id, o.order_date,
           SUM(oi.quantity * oi.unit_price) AS order_amount
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status = 'completed'
    GROUP BY o.order_id, o.customer_id, o.order_date
),
customer_agg AS (
    SELECT customer_id,
           MAX(order_date) AS last_order_date,
           COUNT(*) AS frequency,
           SUM(order_amount) AS monetary
    FROM order_totals
    GROUP BY customer_id
),
rfm_scores AS (
    SELECT
        customer_id,
        (DATE '2025-01-01' - last_order_date) AS recency_days,
        frequency,
        monetary,
        -- чем меньше recency_days, тем выше должен быть балл, поэтому 6 - ntile
        (6 - NTILE(5) OVER (ORDER BY (DATE '2025-01-01' - last_order_date) ASC)) AS r_score,
        NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC) AS m_score
    FROM customer_agg
)
SELECT
    *,
    r_score + f_score + m_score AS rfm_total,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 4 AND f_score >= 3 THEN 'Loyal'
        WHEN r_score <= 2 AND m_score >= 4 THEN 'At risk (high value)'
        WHEN r_score <= 2 AND f_score <= 2 THEN 'Lost'
        ELSE 'Regular'
    END AS segment
FROM rfm_scores
ORDER BY rfm_total DESC;
