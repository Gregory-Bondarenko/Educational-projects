-- Задание 16
CREATE OR REPLACE VIEW monthly_sales_summary AS
SELECT
    date_trunc('month', o.order_date)::date AS month,
    COUNT(DISTINCT o.order_id) FILTER (WHERE o.status = 'completed') AS completed_orders,
    COUNT(DISTINCT o.order_id) FILTER (WHERE o.status = 'cancelled') AS cancelled_orders,
    COUNT(DISTINCT o.order_id) FILTER (WHERE o.status = 'refunded') AS refunded_orders,
    COALESCE(SUM(oi.quantity * oi.unit_price) FILTER (WHERE o.status = 'completed'), 0) AS revenue,
    COUNT(DISTINCT o.customer_id) AS unique_customers
FROM orders o
LEFT JOIN order_items oi ON oi.order_id = o.order_id
GROUP BY month;

SELECT * FROM monthly_sales_summary ORDER BY month;
