"""Общие функции подготовки признаков для ноутбуков 02, 03 и predict.py

Всё, что здесь считается, известно ДО публикации поста. Комментарии, лайки и
просмотры самого поста в признаки не попадают, иначе прогноз «до публикации»
превращается в подглядывание в ответ
"""
from pathlib import Path

import emoji
import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
MODELS_DIR = PROJECT_DIR / "models"

RAW_FILE = DATA_DIR / "vk_posts_raw.xlsx"
PREPARED_FILE = DATA_DIR / "vk_posts_prepared.csv"

# VK начал показывать счётчик просмотров в 2017 году, у более ранних постов там 0
VIEWS_START = pd.Timestamp("2017-01-01")

# Сколько последних постов берём для «текущего уровня» сообщества
MOMENTUM_WINDOW = 20

# Словарь тематик: грубая эвристика по ключевым словам, первая совпавшая тема побеждает
CATEGORY_KEYWORDS = {
    "Матч / Результаты": ["счёт", "счет", "победа", "проигрыш", "проигрываем", "ничья", "гол",
                          "матч", "результат", "состав", "преодолела"],
    "Анонс / Расписание": ["анонс", "начало", "во сколько", "где смотреть", "дата", "стадион"],
    "Праздники / Поздравления": ["поздравляем", "с праздником", "рождество", "новый год", "пасха", "праздник"],
    "Юмор / Мемы": ["мем", "шутка", "угар", "прикол"],
    "Интерактив / Опрос": ["опрос", "проголосуй", "как думаете", "ваше мнение"],
}

META_FEATURES = ["len", "words", "emoji", "hashtags", "links", "has_score", "exclamations",
                 "is_empty", "hours_since_prev", "posts_last_24h"]
CALENDAR_FEATURES = ["hour", "weekday"]


def classify_post(text):
    text = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return category
    return "Другое"


def text_features(texts):
    t = pd.Series(texts, dtype="object").fillna("").astype(str)
    return pd.DataFrame({
        "len": t.str.len(),
        "words": t.str.split().str.len(),
        "emoji": t.apply(emoji.emoji_count),  # настоящие эмодзи, а не любая пунктуация
        "hashtags": t.str.count(r"#\w+"),
        "links": t.str.count(r"https?://|vk\.com|\[club|\[id"),
        "has_score": t.str.contains(r"\b\d{1,2}\s?[:\-]\s?\d{1,2}\b").astype(int),  # «2:1», «5-0»
        "exclamations": t.str.count("!"),
        "is_empty": (t.str.strip() == "").astype(int),
        "category": t.apply(classify_post),
    }, index=t.index)


def load_raw():
    df = pd.read_excel(RAW_FILE)
    df["Текст поста"] = df["Текст поста"].fillna("").astype(str)
    # В сырых данных время в UTC, переводим в московское, в нём же живёт аудитория
    df["Дата публикации"] = pd.to_datetime(df["Дата публикации"]) + pd.Timedelta(hours=3)
    return df.sort_values("Дата публикации").reset_index(drop=True)


def add_features(df):
    """Добавляет признаки к отсортированному по времени датафрейму постов"""
    df = df.copy()
    dt = df["Дата публикации"]
    df["hour"] = dt.dt.hour
    df["weekday"] = dt.dt.dayofweek
    df = pd.concat([df, text_features(df["Текст поста"])], axis=1)

    df["hours_since_prev"] = dt.diff().dt.total_seconds().div(3600).fillna(24).clip(upper=24 * 14)
    df["posts_last_24h"] = (
        pd.Series(1, index=dt).rolling("24h").count().values - 1
    )

    # Текущий уровень сообщества: медиана log-просмотров и log-лайков по прошлым
    # постам. Сдвиг на 1 гарантирует, что сам пост в свою медиану не попадает
    for col, name in [("Просмотры", "views"), ("Лайки", "likes")]:
        logged = np.log1p(df[col])
        df[f"level_{name}"] = logged.shift(1).rolling(MOMENTUM_WINDOW, min_periods=5).median()
    return df
