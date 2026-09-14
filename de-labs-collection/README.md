# Data Engineering Labs Collection

Практические занятия по дисциплине «Инженерия данных» (2 курс, «Прикладная информатика», профиль «Анализ данных»).

Формально задания рассчитаны на аналитическую платформу **Deductor Studio** (GUI-инструмент для ETL). Я делал их на Python в Jupyter — тот же результат (импорт/экспорт, преобразование типов, очистка, агрегация, объединение таблиц), но кодом, а не перетаскиванием узлов. В каждом отчёте это явно оговорено.

## Раздел 1 — основы работы с данными

| Ноутбук | Что делает |
|---|---|
| [01_import_export_types.ipynb](./section1-data-basics/01_import_export_types.ipynb) | Импорт CSV без заголовков → разметка колонок → экспорт в TXT → повторный импорт → приведение столбца к булеву типу |
| [02_filter_clean_credit_data.ipynb](./section1-data-basics/02_filter_clean_credit_data.ipynb) | Работа с датасетом заявок на кредит: статистика, пропуски, замена значений в категориальных полях, комбинированная фильтрация, сортировка |
| [03_feature_engineering_credit_data.ipynb](./section1-data-basics/03_feature_engineering_credit_data.ipynb) | Производные признаки: дата обработки, пересчёт суммы в у.е., булевы флаги по условиям, сегментация заёмщиков по правилам |

## Раздел 2 — трансформация данных

| Ноутбук | Что делает |
|---|---|
| [01_sliding_window_features.ipynb](./section2-data-transformation/01_sliding_window_features.ipynb) | Скользящее окно: лаги и значения "вперёд" для одного и нескольких временных рядов |
| [02_eda_credit_visualizations.ipynb](./section2-data-transformation/02_eda_credit_visualizations.ipynb) | Разведочный анализ: суммы кредитов по неделям в разрезе цели кредита и возрастных групп |
| [03_grouping_aggregation.ipynb](./section2-data-transformation/03_grouping_aggregation.ipynb) | Фильтрация, группировка и агрегация (по дате, клиенту, товару) |
| [04_union_join_deduplication.ipynb](./section2-data-transformation/04_union_join_deduplication.ipynb) | Объединение таблиц с разной структурой (union), inner/left join, поиск дублей и противоречивых записей по ключу |

Каждый ноутбук сопровождается отчётом (`reports/`) с постановкой задачи и выводами

## Стек

Python, pandas, numpy, matplotlib, seaborn
