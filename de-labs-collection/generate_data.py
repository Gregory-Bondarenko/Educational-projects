"""Синтетические версии учебных датасетов из методички к Deductor Studio

Оригинальные CreditSample.txt и Credit.txt идут в поставке Deductor и в репозиторий
не входят. Скрипт создаёт файлы той же структуры (TSV, cp1251), чтобы ноутбуки
запускались от начала до конца. Цифры в выводах ноутбуков поэтому отличаются
от цифр в отчётах

Запуск из папки de-labs-collection:
    python generate_data.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
rng = np.random.default_rng(2024)

GOALS = ["Покупка товара", "Оплата за образование", "Оплата услуг (мед., юрид. и т.п.)",
         "Покупка и ремонт недвижимости", "Покупка автомобиля", "Иное"]
SPENDING = ["Покупка товаров длит. пользования", "Содержание/аренда недвижимости, а/т",
            "Затраты на образование (в т.ч. детей)", "Турпоездки, развлечения и т.п.",
            "Выплаты по кредитам/займам"]


def input_csv():
    path = ROOT / "section1-data-basics" / "data" / "input.csv"
    path.write_text("a,1,4.5,b,c,26/04/2011,d\na1,0,5,b1,c1,,d1\n", encoding="utf-8")


def credit_sample(n=200):
    income = rng.integers(4, 40, n) * 500
    df = pd.DataFrame({
        "Код": np.arange(1, n + 1),
        "Размер ссуды, руб": rng.integers(4, 60, n) * 500,
        "Срок ссуды, мес": rng.choice([6, 12, 18, 24, 36], n),
        "Цель ссуды": rng.choice(GOALS, n, p=[0.3, 0.15, 0.15, 0.15, 0.1, 0.15]),
        "Среднемесячный доход, руб": income,
        "Среднемесячный расход, руб": (income * rng.uniform(0.3, 0.9, n) // 500 * 500).astype(int),
        "Основное направление расходов": rng.choice(SPENDING, n),
        "Количество лет": rng.integers(19, 70, n),
        "Семейное положение": rng.choice(["Да", "Нет"], n),
        "Количество иждивенцев": rng.choice([0, 1, 2, 3], n, p=[0.4, 0.3, 0.2, 0.1]),
        "Наличие недвижимости": rng.choice(["Да", "Нет"], n, p=[0.4, 0.6]),
        "Давать кредит": rng.choice(["ИСТИНА", "ЛОЖЬ"], n, p=[0.65, 0.35]),
    })
    df.to_csv(ROOT / "section1-data-basics" / "data" / "CreditSample.txt",
              sep="\t", index=False, encoding="cp1251")


def credit(n=600):
    dates = pd.Timestamp("2002-12-20") + pd.to_timedelta(rng.integers(0, 400, n), unit="D")
    amount = rng.integers(4, 60, n) * 500
    term = rng.choice([6, 12, 18, 24], n)
    income = rng.integers(4, 30, n) * 500
    df = pd.DataFrame({
        "Сумма кредита": amount,
        "Стоимость кредита": (amount * 0.2).astype(int),
        "Срок кредита": term,
        "Дата кредитования": dates.strftime("%d.%m.%y"),
        "Цель кредитования": rng.choice(GOALS, n),
        "Количество": 1,
        "Возраст": rng.integers(18, 75, n),
        "Пол": rng.choice(["Муж", "Жен"], n),
        "Образование": rng.choice(["среднее", "специальное", "высшее"], n),
        "Частная собственность": rng.choice(["Да", "Нет"], n),
        "Срок работы по специальности": rng.integers(0, 30, n),
        "Среднемес. доход": income,
        "Среднемес. расход": (income * rng.uniform(0.3, 0.8, n) // 500 * 500).astype(int),
        "Основное направление расходов": rng.choice(SPENDING, n),
    }).sort_values("Дата кредитования", key=lambda s: pd.to_datetime(s, format="%d.%m.%y"))
    df.to_csv(ROOT / "section2-data-transformation" / "data" / "Credit.txt",
              sep="\t", index=False, encoding="cp1251")


if __name__ == "__main__":
    input_csv()
    credit_sample()
    credit()
    print("Готово: input.csv, CreditSample.txt, Credit.txt")
