-- Часть 5. Воронка продаж и рекурсивные запросы

-- Задание 14. Воронка: сколько сессий дошло до каждого шага
-- (visit -> view_product -> add_to_cart -> checkout_start -> purchase)
-- и конверсия к предыдущему шагу
WITH stage_order AS (
    SELECT session_id,
        CASE event_type
            WHEN 'visit' THEN 1
            WHEN 'view_product' THEN 2
            WHEN 'add_to_cart' THEN 3
            WHEN 'checkout_start' THEN 4
            WHEN 'purchase' THEN 5
        END AS stage_no
    FROM events
),
session_max AS (
    SELECT session_id, MAX(stage_no) AS max_stage FROM stage_order GROUP BY session_id
),
stages(stage_no, event_type) AS (
    VALUES (1,'visit'), (2,'view_product'), (3,'add_to_cart'), (4,'checkout_start'), (5,'purchase')
),
funnel AS (
    SELECT st.stage_no, st.event_type, COUNT(*) AS sessions_reached
    FROM session_max sm
    JOIN stages st ON st.stage_no <= sm.max_stage
    GROUP BY st.stage_no, st.event_type
)
SELECT
    stage_no,
    event_type,
    sessions_reached,
    ROUND(sessions_reached::numeric / LAG(sessions_reached) OVER (ORDER BY stage_no) * 100, 1) AS conversion_from_prev_pct
FROM funnel
ORDER BY stage_no;

-- Задание 15. Реферальная сеть: у клиентов есть поле referred_by
-- (кто кого пригласил). Recursive CTE строит дерево от каждого
-- "самостоятельного" клиента и считает размер его сети приглашений.
WITH RECURSIVE referral_tree AS (
    SELECT customer_id, customer_id AS root_id, 1 AS depth
    FROM customers
    WHERE referred_by IS NULL

    UNION ALL

    SELECT c.customer_id, rt.root_id, rt.depth + 1
    FROM customers c
    JOIN referral_tree rt ON c.referred_by = rt.customer_id
)
SELECT
    rt.root_id,
    root.full_name,
    COUNT(*) - 1 AS network_size,
    MAX(rt.depth) - 1 AS max_depth
FROM referral_tree rt
JOIN customers root ON root.customer_id = rt.root_id
GROUP BY rt.root_id, root.full_name
HAVING COUNT(*) - 1 > 0
ORDER BY network_size DESC
LIMIT 15;
