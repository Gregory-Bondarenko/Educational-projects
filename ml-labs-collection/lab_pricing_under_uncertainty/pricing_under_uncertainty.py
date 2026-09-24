from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

OUT_DIR = Path(__file__).resolve().parent

#Исходные данные
q0 = 100        #базовый спрос
p0 = 10         #базовая цена
Mb = 2          #мат ожидание b
Ma = 0          #мат ожидание a
sigma_a = 0.5   #СКО возмущения a
sigma_b = 0.2   #СКО возмущения b

#Оптимальная цена по максимальному среднему доходу
p_opt_mean = (q0 + Mb * p0) / (2 * Mb)
print(f"Оптимальная цена по максимальному среднему доходу: p* = {p_opt_mean:.2f}")

#Аналитическая форма дохода
def revenue(p, a, b):
    """Функция дохода R(p) = p * ((q0 + a) - b*(p - p0))"""
    return p * ((q0 + a) - b * (p - p0))

#Таблица дохода при фиксированном p=26 и разных a,b
p_fixed = 26
a_vals = np.linspace(-1, 1, 11)
b_vals = np.linspace(1.6, 2.4, 5)

table = pd.DataFrame(
    [[revenue(p_fixed, a, b) for b in b_vals] for a in a_vals],
    index=[f"{a:.1f}" for a in a_vals],
    columns=[f"{b:.1f}" for b in b_vals]
)

print("\nТаблица доходов при p = 26:")
print(table.round(1))

#Симуляция для стохастической оценки
N = 100_000
rng = np.random.default_rng(42)
a_samples = rng.normal(Ma, sigma_a, N)
b_samples = rng.normal(Mb, sigma_b, N)

prices = np.linspace(15, 40, 200)
revenues = np.zeros((len(prices), N))

for i, p in enumerate(prices):
    revenues[i, :] = revenue(p, a_samples, b_samples)

mean_revenue = revenues.mean(axis=1)
p_opt_stoch = prices[np.argmax(mean_revenue)]

print(f"\nОптимальная цена по симуляции (ожидаемый доход): p ≈ {p_opt_stoch:.2f}")

#Обеспечить приемлемый доход с максимальной вероятностью
R_min = 1700
prob = (revenues >= R_min).mean(axis=1)
p_opt_prob = prices[np.argmax(prob)]

print(f"Цена, обеспечивающая максимальную вероятность дохода ≥ {R_min}: p ≈ {p_opt_prob:.2f}")

#Визуализация
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
plt.sca(ax1)
plt.plot(prices, mean_revenue, label='Средний доход', lw=2)
plt.axvline(p_opt_stoch, color='r', ls='--', label=f'p* (mean) = {p_opt_stoch:.1f}')
plt.xlabel("Цена p")
plt.ylabel("Средний доход R")
plt.title("Оптимизация ожидаемого дохода")
plt.legend()
plt.grid(True)

plt.sca(ax2)
plt.plot(prices, prob, color='purple', lw=2)
plt.axvline(p_opt_prob, color='r', ls='--', label=f'p* (prob) = {p_opt_prob:.1f}')
plt.xlabel("Цена p")
plt.ylabel(f"P(R ≥ {R_min})")
plt.title("Вероятность получить приемлемый доход")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(OUT_DIR / 'result.png', dpi=120, bbox_inches='tight')
plt.show()