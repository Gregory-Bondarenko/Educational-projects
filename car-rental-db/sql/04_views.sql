-- Представления под разные роли

-- Менеджерам: текущие и подтверждённые аренды с контактами клиента
CREATE OR REPLACE VIEW manager_rentals_view AS
SELECT
    r.id                               AS rental_number,
    c.first_name || ' ' || c.last_name AS client_name,
    c.phone                            AS client_phone,
    ca.brand || ' ' || ca.model        AS car_info,
    r.start_date,
    r.end_date,
    r.total_cost,
    r.status
FROM rentals r
JOIN clients c ON r.client_id = c.id
JOIN cars ca   ON r.car_id = ca.id
WHERE r.status IN ('active', 'confirmed');

-- Финансовому отделу: платежи по завершённым арендам без персональных данных клиентов
CREATE OR REPLACE VIEW finance_payments_view AS
SELECT
    p.id          AS payment_id,
    p.rental_id,
    p.payment_date,
    p.amount,
    p.payment_type,
    r.total_cost  AS rental_total
FROM payments p
JOIN rentals r ON p.rental_id = r.id
WHERE r.status = 'completed';

-- CRM: сколько раз клиент арендовал и сколько потратил
CREATE OR REPLACE VIEW client_analysis_view AS
SELECT
    c.id                               AS client_id,
    c.first_name || ' ' || c.last_name AS client_name,
    COUNT(r.id)                        AS total_rentals,
    COALESCE(SUM(r.total_cost), 0)     AS total_spent,
    MIN(r.start_date)                  AS first_rental,
    MAX(r.start_date)                  AS last_rental
FROM clients c
LEFT JOIN rentals r ON c.id = r.client_id AND r.status = 'completed'
GROUP BY c.id, c.first_name, c.last_name;
