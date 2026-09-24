from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize

OUT_DIR = Path(__file__).resolve().parent

def minkowski_fit(x, y, p=2):

    def loss(params):
        a, b = params
        residuals = y - (a * x + b)
        return np.sum(np.abs(residuals)**p)
    
    #Начальное приближение (L2-решение)
    A = np.vstack([x, np.ones(len(x))]).T
    a_l2, b_l2 = np.linalg.lstsq(A, y, rcond=None)[0]
    
    #Оптимизация
    #При p <= 1 функция потерь негладкая, градиентные методы (BFGS) на ней
    #останавливаются где попало, поэтому берём безградиентный Nelder-Mead
    method = 'Nelder-Mead' if p <= 1 else 'BFGS'
    result = minimize(loss, [a_l2, b_l2], method=method, options={'xatol': 1e-8, 'fatol': 1e-10, 'maxiter': 10000} if method == 'Nelder-Mead' else None)
    a_opt, b_opt = result.x
    
    return a_opt, b_opt

#Генерация данных
np.random.seed(42)
x = np.linspace(0, 4, 20)
y_true = 1.2 * x + 0.8
y_noise = y_true + np.random.normal(0, 0.3, len(x))

y_noise[10] += 3.0

#Значения p для сравнения
p_values = [1, 1.5, 2, 5]
colors = ['red', 'green', 'blue', 'purple']

#График
plt.figure(figsize=(10, 6))
plt.scatter(x, y_noise, color='black', label='Данные (с выбросом)', zorder=3)

#Истинная прямая
plt.plot(x, y_true, '--', color='gray', label='Истинная прямая', alpha=0.7)

#Аппроксимация для разных p
for p, color in zip(p_values, colors):
    a, b = minkowski_fit(x, y_noise, p=p)
    y_fit = a * x + b
    plt.plot(x, y_fit, color=color, label=f'L{p}: y = {a:.2f}x + {b:.2f}')
    print(f'p = {p}: y = {a:.3f}x + {b:.3f}')

plt.title('Аппроксимация прямой с разными нормами Минковского')
plt.xlabel('x')
plt.ylabel('y')
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend()
plt.savefig(OUT_DIR / 'result.png', dpi=120, bbox_inches='tight')
plt.show()