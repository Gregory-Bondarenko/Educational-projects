import numpy as np
import matplotlib.pyplot as plt

#Входные параметры
p0 = 0.2
p1 = 0.3
p2 = 0.5
n = 100          #t0
trials = 20000   #количество симуляций

#Теоритическое значение
E_step = p2 - p1
Var_step = (p1 + p2) - (p2 - p1)**2
E_n = n * E_step
Var_n = n * Var_step

print(f"Теоретическое E[X_n] = {E_n}")
print(f"Теоретическая Var(X_n) = {Var_n}")

#Симуляция
rng = np.random.default_rng(42)
moves = np.array([0, -1, +1])
probs = [p0, p1, p2]
final_positions = np.empty(trials)

for i in range(trials):
    steps = rng.choice(moves, size=n, p=probs)
    final_positions[i] = np.sum(steps)

#Эмпирические значения
emp_mean = np.mean(final_positions)
emp_var = np.var(final_positions)

print(f"Эмпирическое E[X_n] = {emp_mean:.4f}")
print(f"Эмпирическая Var(X_n) = {emp_var:.4f}")

#Визуализация распределения
plt.hist(final_positions, bins=50, color="orange", edgecolor="black", density=True)
plt.title(f"Гистограмма распределения X_n (n={n})")
plt.xlabel("Положение X_n")
plt.ylabel("Плотность вероятности")
plt.grid(True)
plt.show()