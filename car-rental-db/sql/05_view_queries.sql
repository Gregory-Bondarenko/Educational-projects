-- Запросы поверх представлений

-- Какие машины на руках у клиентов на заданную дату
-- Дата задана явно: данные в наполнении заканчиваются ноябрём 2025
SELECT *
FROM manager_rentals_view
WHERE status = 'active'
  AND DATE '2025-11-10' BETWEEN start_date AND end_date
ORDER BY start_date;

-- Сегменты клиентов по числу аренд
SELECT
    client_name,
    total_rentals,
    total_spent,
    CASE
        WHEN total_rentals >= 3 THEN 'VIP клиент'
        WHEN total_rentals = 2  THEN 'Постоянный клиент'
        WHEN total_rentals = 1  THEN 'Новый клиент'
        ELSE 'Потенциальный клиент'
    END AS client_category
FROM client_analysis_view
WHERE total_rentals > 0
ORDER BY total_spent DESC;

-- Сверка: сумма платежей по каждой завершённой аренде против её стоимости
SELECT
    rental_id,
    rental_total,
    SUM(amount)                AS paid,
    rental_total - SUM(amount) AS debt
FROM finance_payments_view
GROUP BY rental_id, rental_total
ORDER BY rental_id;
