# Лабораторные по инженерии данных

Практические задания по дисциплине «Инженерия данных», 2 курс (2025). По программе они рассчитаны на Deductor Studio, где ETL собирается из узлов мышкой. Здесь то же самое сделано на pandas: импорт и экспорт, типы, очистка, вычисляемые поля, скользящее окно, группировка, слияние таблиц, поиск дублей

Задачи простые, это самое начало работы с данными

## Раздел 1. Основы работы с данными

| Ноутбук | Что делает |
|---|---|
| [01_import_export_types](./section1-data-basics/01_import_export_types.ipynb) | CSV без заголовков, разметка столбцов, выгрузка в TXT и обратно, приведение столбца к логическому типу |
| [02_filter_clean_credit_data](./section1-data-basics/02_filter_clean_credit_data.ipynb) | Заявки на кредит: статистика, пропуски, замена значений в категориальных полях, фильтр вида «a или b», сортировка |
| [03_feature_engineering_credit_data](./section1-data-basics/03_feature_engineering_credit_data.ipynb) | Вычисляемые поля: дата обработки, сумма в у.е., флаги по условиям, сегментация заёмщиков по правилам |

## Раздел 2. Трансформация данных

| Ноутбук | Что делает |
|---|---|
| [01_sliding_window_features](./section2-data-transformation/01_sliding_window_features.ipynb) | Скользящее окно: лаги и значение на шаг вперёд для одного и нескольких рядов |
| [02_eda_credit_visualizations](./section2-data-transformation/02_eda_credit_visualizations.ipynb) | Год и неделя из даты, суммы кредитов по неделям в разрезе целей, квантование возраста на 5 интервалов |
| [03_grouping_aggregation](./section2-data-transformation/03_grouping_aggregation.ipynb) | Фильтрация, группировка продаж по дате, клиенту и товару |
| [04_union_join_deduplication](./section2-data-transformation/04_union_join_deduplication.ipynb) | Union таблиц с разной структурой, inner и left join, дубликаты и противоречия по ключу |

## Запуск

```bash
pip install -r requirements.txt
python generate_data.py
```

Дальше ноутбуки открываются из своих папок и запускаются по порядку номеров. Отчёты в Word лежат в `reports/` внутри каждого раздела

Стек: Python, pandas, numpy, matplotlib, seaborn
