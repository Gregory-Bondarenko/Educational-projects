-- Типовые запросы сервиса аренды

-- 1. Свободные автомобили эконом-класса (до 3000 ₽/сутки) на 20 ноября 2025
SELECT
    c.brand         AS Марка,
    c.model         AS Модель,
    c.year          AS Год,
    c.daily_rate    AS "Цена за сутки",
    c.license_plate AS "Госномер"
FROM cars c
WHERE c.status = 'available'
  AND c.daily_rate < 3000
  AND NOT EXISTS (
      SELECT 1
      FROM rentals r
      WHERE r.car_id = c.id
        AND r.status IN ('active', 'confirmed')
        AND DATE '2025-11-20' BETWEEN r.start_date AND r.end_date
  )
ORDER BY c.daily_rate;

-- 2. Свободна ли конкретная модель на нужную дату
SELECT
    c.brand         AS Марка,
    c.model         AS Модель,
    c.license_plate AS "Госномер",
    c.daily_rate    AS "Цена за сутки",
    c.status        AS Статус
FROM cars c
WHERE c.brand = 'Toyota'
  AND c.model = 'Camry'
  AND c.status = 'available'
  AND c.id NOT IN (
      SELECT r.car_id
      FROM rentals r
      WHERE DATE '2025-11-25' BETWEEN r.start_date AND r.end_date
        AND r.status IN ('active', 'confirmed')
  );

-- 3. Помесячная выручка по завершённым арендам
SELECT
    TO_CHAR(r.start_date, 'YYYY-MM')                 AS "Месяц",
    COUNT(r.id)                                      AS "Количество аренд",
    SUM(r.total_cost)                                AS "Общая выручка",
    ROUND(AVG(r.total_cost), 2)                      AS "Средний чек",
    ROUND(AVG(r.end_date - r.start_date), 1)         AS "Средняя продолжительность (дней)"
FROM rentals r
WHERE r.status = 'completed'
  AND r.start_date >= DATE '2025-01-01'
GROUP BY TO_CHAR(r.start_date, 'YYYY-MM')
ORDER BY "Месяц" DESC;

-- 4. Текущие и завершённые аренды с клиентом и машиной
SELECT
    r.id                               AS "Номер аренды",
    c.first_name || ' ' || c.last_name AS Клиент,
    ca.brand || ' ' || ca.model        AS Автомобиль,
    r.start_date                       AS "Дата начала",
    r.end_date                         AS "Дата окончания",
    (r.end_date - r.start_date)        AS "Длительность (дней)",
    r.total_cost                       AS Стоимость,
    r.status                           AS Статус
FROM rentals r
JOIN clients c ON r.client_id = c.id
JOIN cars ca   ON r.car_id = ca.id
WHERE r.status IN ('active', 'completed')
ORDER BY r.start_date DESC;

-- 5. Обновление контактов клиента
UPDATE clients
SET phone = '+79998887766',
    email = 'new_email@example.com'
WHERE id = 1
RETURNING id, first_name, last_name, phone, email;

-- 6. Параметризованный поиск клиента по телефону
PREPARE find_client_by_phone (VARCHAR) AS
    SELECT * FROM clients WHERE phone = $1;

EXECUTE find_client_by_phone('+79997654321');
DEALLOCATE find_client_by_phone;

-- 7. Сезонность: аренды, популярные марки и выручка по месяцам 2025 года
SELECT
    EXTRACT(MONTH FROM r.start_date)    AS "Месяц",
    COUNT(r.id)                         AS "Количество аренд",
    STRING_AGG(DISTINCT ca.brand, ', ') AS "Марки",
    ROUND(AVG(ca.daily_rate), 2)        AS "Средняя цена аренды",
    SUM(r.total_cost)                   AS "Общая выручка"
FROM rentals r
JOIN cars ca ON r.car_id = ca.id
WHERE r.status = 'completed'
  AND EXTRACT(YEAR FROM r.start_date) = 2025
GROUP BY EXTRACT(MONTH FROM r.start_date)
ORDER BY "Количество аренд" DESC, "Месяц";
