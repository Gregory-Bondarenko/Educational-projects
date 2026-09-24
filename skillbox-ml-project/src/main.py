"""Консольный прогноз: совершит ли посетитель сайта целевое действие.

Запуск из корня проекта:
    python src/main.py
"""
import pickle
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
ENCODERS_DIR = ROOT / "encoders"
MODEL_PATH = ROOT / "model" / "model.pickle"

# Порядок признаков совпадает с порядком колонок, на которых училась модель
FEATURES = [
    "utm_source", "utm_medium", "utm_campaign", "utm_adcontent",
    "device_category", "device_brand", "device_screen_resolution",
    "device_browser", "geo_country", "geo_city",
]
CATEGORICAL = [f for f in FEATURES if f != "device_screen_resolution"]

# Значение, которого не было в обучающей выборке, кодируем как -1
UNKNOWN = -1


def load_encoders():
    encoders = {}
    for col in CATEGORICAL:
        with open(ENCODERS_DIR / f"{col}_encoder.pickle", "rb") as f:
            encoders[col] = pickle.load(f)
    return encoders


def load_model():
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)


def parse_resolution(value):
    """'1920x1080' -> площадь экрана в пикселях"""
    width, height = value.lower().replace("х", "x").split("x")
    return int(width) * int(height)


def ask_user(encoders):
    print("Введите данные пользователя\n")
    row = {}
    for col in FEATURES:
        while True:
            value = input(f"{col}: ").strip()
            if col == "device_screen_resolution":
                try:
                    row[col] = parse_resolution(value)
                    break
                except ValueError:
                    print("Нужен формат ШИРИНАxВЫСОТА, например 1920x1080\n")
            else:
                row[col] = encoders[col].get(value, UNKNOWN)
                break
    return pd.DataFrame([row], columns=FEATURES)


def main():
    encoders = load_encoders()
    model = load_model()

    while True:
        print()
        user = ask_user(encoders)
        proba = model.predict_proba(user)[0, 1]
        verdict = "совершит" if proba >= 0.5 else "не совершит"
        print(f"\nПрогноз: пользователь {verdict} целевое действие (вероятность {proba:.2f})\n")

        if input("Проверить ещё одного пользователя? (да/нет): ").strip().lower() != "да":
            break


if __name__ == "__main__":
    main()
