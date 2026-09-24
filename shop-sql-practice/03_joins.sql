-- Часть 1. JOIN

-- Задание 1. Вывести заказы вместе с именем клиента и статусом (INNER JOIN)
SELECT o.order_id, c.full_name, o.order_date, o.status
FROM orders o
INNER JOIN customers c ON c.customer_id = o.customer_id
ORDER BY o.order_date
LIMIT 20;

-- Задание 2. Найти клиентов, которые ни разу не сделали заказ (LEFT JOIN)
SELECT c.customer_id, c.full_name, c.signup_date
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
WHERE o.order_id IS NULL;

-- Задание 3. Найти товары, которые ни разу не заказывали (RIGHT JOIN)
SELECT p.product_id, p.name
FROM order_items oi
RIGHT JOIN products p ON p.product_id = oi.product_id
WHERE oi.order_item_id IS NULL;

-- Задание 4. Полное сопоставление клиентов и заказов, включая тех,
-- у кого заказов нет, и заказы без привязки (на случай "битых" данных) (FULL JOIN)
SELECT c.customer_id, o.order_id
FROM customers c
FULL JOIN orders o ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL OR o.order_id IS NULL;

-- Задание 5 (доп). В одном запросе: JOIN + оконная функция.
-- Для каждого клиента считаем сумму его заказов и сразу ранжируем
-- клиентов внутри страны по этой сумме.
SELECT
    c.customer_id,
    c.full_name,
    c.country,
    COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS total_spent,
    RANK() OVER (PARTITION BY c.country ORDER BY COALESCE(SUM(oi.quantity * oi.unit_price), 0) DESC) AS rank_in_country
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id AND o.status = 'completed'
LEFT JOIN order_items oi ON oi.order_id = o.order_id
GROUP BY c.customer_id, c.full_name, c.country
ORDER BY c.country, rank_in_country;
