-- Наполнение таблиц данными за 2023-2024 год.
-- В реальности такой датасет обычно выгружают из системы магазина,
-- здесь генерируем сами, чтобы было воспроизводимо.

SELECT setseed(0.42);

-- клиенты, регистрация с начала 2023 до середины 2024
INSERT INTO customers (full_name, email, country, signup_date)
SELECT
    'Customer ' || i,
    'customer' || i || '@mail.test',
    (ARRAY['US','DE','FR','GB','ES','IT','PL','NL'])[1 + floor(random() * 8)::int],
    DATE '2023-01-01' + floor(random() * 540)::int
FROM generate_series(1, 1500) AS i;

-- часть клиентов пришла по приглашению одного из предыдущих 100 клиентов
UPDATE customers c
SET referred_by = c.customer_id - (1 + floor(random() * LEAST(c.customer_id - 1, 100)))::int
WHERE c.customer_id > 1
  AND random() < 0.35;

-- товарный каталог
INSERT INTO products (name, category, price)
SELECT
    'Product ' || i,
    (ARRAY['Electronics','Home','Beauty','Sports','Books','Toys'])[1 + floor(random() * 6)::int],
    round((5 + random() * 495)::numeric, 2)
FROM generate_series(1, 80) AS i;

-- заказы, дата не позже конца 2024; у части клиентов заказов нет совсем
-- (слагаемое 0 * id нужно, чтобы random() пересчитывался для каждой строки,
-- иначе PostgreSQL вычислит подзапрос в LATERAL один раз на всех)
INSERT INTO orders (customer_id, order_date, status)
SELECT
    c.customer_id,
    LEAST(c.signup_date + floor(random() * 400)::int, DATE '2024-12-31'),
    (ARRAY['completed','completed','completed','completed','cancelled','refunded'])[1 + floor(random() * 6)::int]
FROM customers c
JOIN LATERAL generate_series(1, floor(random() * 6 + 0 * c.customer_id)::int) AS g(n) ON true;

-- состав заказов, 1-4 товара в заказе
INSERT INTO order_items (order_id, product_id, quantity, unit_price)
SELECT
    o.order_id,
    p.product_id,
    (1 + floor(random() * 3))::int,
    p.price
FROM orders o
JOIN LATERAL (
    SELECT product_id, price FROM products
    ORDER BY random() + 0 * o.order_id
    LIMIT (1 + floor(random() * 4 + 0 * o.order_id))::int
) p ON true;

-- товары, которые добавили в каталог, но так и не продали
INSERT INTO products (name, category, price) VALUES
    ('Product 81', 'Toys', 19.99),
    ('Product 82', 'Books', 7.50);

-- сессии на сайте: у каждого клиента 1-4 сессии, каждая доходит
-- до какой-то стадии воронки (от простого захода до покупки)
CREATE TEMP TABLE temp_sessions AS
SELECT
    row_number() OVER () AS session_id,
    c.customer_id,
    (LEAST(c.signup_date + floor(random() * 400)::int, DATE '2024-12-31'))::timestamp
        + (random() * interval '18 hours') AS session_start,
    random() AS r
FROM customers c
JOIN LATERAL generate_series(1, (1 + floor(random() * 4 + 0 * c.customer_id))::int) AS g(n) ON true;

INSERT INTO events (customer_id, session_id, event_type, event_time)
SELECT
    ts.customer_id,
    ts.session_id,
    stage.event_type,
    ts.session_start + (stage.stage_no - 1) * (random() * interval '4 minutes')
FROM temp_sessions ts
JOIN (VALUES (1,'visit'), (2,'view_product'), (3,'add_to_cart'), (4,'checkout_start'), (5,'purchase'))
    AS stage(stage_no, event_type)
    ON stage.stage_no <= (
        CASE
            WHEN ts.r < 0.10 THEN 1
            WHEN ts.r < 0.35 THEN 2
            WHEN ts.r < 0.55 THEN 3
            WHEN ts.r < 0.70 THEN 4
            ELSE 5
        END
    );

DROP TABLE temp_sessions;
