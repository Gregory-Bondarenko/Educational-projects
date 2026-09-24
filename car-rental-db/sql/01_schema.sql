-- Схема БД сервиса аренды автомобилей (PostgreSQL)
--
-- База создаётся отдельно, например:
--   CREATE DATABASE car_rental_db ENCODING 'UTF8' TEMPLATE template0;
-- затем: psql -d car_rental_db -f 01_schema.sql

DROP VIEW IF EXISTS manager_rentals_view, finance_payments_view, client_analysis_view;
DROP TABLE IF EXISTS payments, rentals, cars, clients;

-- Таблица Клиенты
CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    last_name VARCHAR(50) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    passport VARCHAR(20) UNIQUE NOT NULL,
    driver_license VARCHAR(20) UNIQUE NOT NULL,
    phone VARCHAR(15) NOT NULL,
    email VARCHAR(100),
    registration_date DATE DEFAULT CURRENT_DATE
);

-- Таблица Автомобили
CREATE TABLE cars (
    id SERIAL PRIMARY KEY,
    brand VARCHAR(50) NOT NULL,
    model VARCHAR(50) NOT NULL,
    year INTEGER NOT NULL CHECK (year >= 2000),
    license_plate VARCHAR(15) UNIQUE NOT NULL,
    vin VARCHAR(17) UNIQUE,
    daily_rate DECIMAL(10,2) NOT NULL CHECK (daily_rate > 0),
    status VARCHAR(20) DEFAULT 'available'
        CHECK (status IN ('available', 'rented', 'maintenance'))
);

-- Таблица Аренды
CREATE TABLE rentals (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(id),
    car_id INTEGER NOT NULL REFERENCES cars(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_cost DECIMAL(10,2) NOT NULL CHECK (total_cost > 0),
    status VARCHAR(20) DEFAULT 'confirmed'
        CHECK (status IN ('confirmed', 'active', 'completed', 'cancelled')),
    CONSTRAINT check_dates CHECK (end_date > start_date)
);

-- Таблица Платежи
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    rental_id INTEGER NOT NULL REFERENCES rentals(id),
    amount DECIMAL(10,2) NOT NULL CHECK (amount > 0),
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payment_type VARCHAR(20)
        CHECK (payment_type IN ('deposit', 'payment', 'fine'))
);

-- Индексы по внешним ключам и датам: по ним идут все отчёты и проверка доступности
CREATE INDEX idx_rentals_client ON rentals (client_id);
CREATE INDEX idx_rentals_car_dates ON rentals (car_id, start_date, end_date);
CREATE INDEX idx_payments_rental ON payments (rental_id);
