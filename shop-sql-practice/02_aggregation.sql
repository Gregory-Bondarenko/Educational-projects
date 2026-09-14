-- Задание 6
SELECT
    date_trunc('month', o.order_date)::date AS month,
    SUM(oi.quantity * oi.unit_price) AS revenue,
    COUNT(DISTINCT o.order_id) AS orders_count
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.status = 'completed'
GROUP BY month
ORDER BY month;

-- Задание 7
SELECT
    p.name,
    p.category,
    SUM(oi.quantity * oi.unit_price) AS revenue
FROM order_items oi
JOIN orders o ON o.order_id = oi.order_id
JOIN products p ON p.product_id = oi.product_id
WHERE o.status = 'completed'
GROUP BY p.product_id, p.name, p.category
ORDER BY revenue DESC
LIMIT 10;

-- Задание 8
SELECT
    c.country,
    ROUND(AVG(order_total), 2) AS avg_order_value
FROM (
    SELECT o.order_id, o.customer_id, SUM(oi.quantity * oi.unit_price) AS order_total
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status = 'completed'
    GROUP BY o.order_id, o.customer_id
) order_totals
JOIN customers c ON c.customer_id = order_totals.customer_id
GROUP BY c.country
ORDER BY avg_order_value DESC;
