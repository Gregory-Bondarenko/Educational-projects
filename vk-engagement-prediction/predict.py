"""Прогноз просмотров и лайков поста до публикации

Пример:
    python predict.py --text "Победа 2:1! Поздравляем команду 🇷🇸" --when "2025-08-10 21:00"

Без аргументов спросит текст и время в консоли
"""
import argparse
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent / "pipeline"))
from features import MODELS_DIR, MOMENTUM_WINDOW, PREPARED_FILE, text_features  # noqa: E402


def community_level(history, when):
    """Медиана log-метрик по последним постам до момента публикации"""
    past = history[history["Дата публикации"] < when].tail(MOMENTUM_WINDOW)
    if past.empty:
        past = history.tail(MOMENTUM_WINDOW)
    return {
        "views": np.log1p(past["Просмотры"]).median(),
        "likes": np.log1p(past["Лайки"]).median(),
        "last_post": past["Дата публикации"].max(),
        "posts_24h": int((past["Дата публикации"] > when - pd.Timedelta(hours=24)).sum()),
    }


def build_row(text, when, level):
    row = text_features([text]).iloc[0].to_dict()
    row["text"] = text.lower()
    row["hour"] = when.hour
    row["weekday"] = when.dayofweek
    hours = (when - level["last_post"]).total_seconds() / 3600
    row["hours_since_prev"] = float(np.clip(hours, 0, 24 * 14))
    row["posts_last_24h"] = level["posts_24h"]
    return pd.DataFrame([row])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--text", help="текст поста")
    parser.add_argument("--when", help="дата и время публикации по Москве, например '2025-08-10 21:00'")
    args = parser.parse_args()

    text = args.text if args.text is not None else input("Текст поста: ")
    when_raw = args.when or input("Когда публикуем (ГГГГ-ММ-ДД ЧЧ:ММ, МСК): ")
    when = pd.Timestamp(when_raw)

    models = joblib.load(MODELS_DIR / "engagement_model.joblib")
    history = pd.read_csv(PREPARED_FILE, parse_dates=["Дата публикации"])
    level = community_level(history, when)
    row = build_row(text, when, level)

    print(f"\nТематика по словарю: {row['category'].iloc[0]}")
    print(f"Длина текста: {row['len'].iloc[0]} символов, эмодзи: {row['emoji'].iloc[0]}")
    for name, title in [("views", "Просмотры"), ("likes", "Лайки")]:
        base = np.expm1(level[name])
        pred = np.expm1(level[name] + models[name].predict(row)[0])
        print(f"{title}: ~{pred:,.0f} (обычный уровень сейчас ~{base:,.0f})".replace(",", " "))


if __name__ == "__main__":
    main()
