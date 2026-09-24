from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

OUT_DIR = Path(__file__).resolve().parent

Sx = 0.0   #сумма всех x
Sy = 0.0   #сумма всех y
Sxx = 0.0  #сумма x^2
Sxy = 0.0  #сумма x*y
n = 0  #количество точек

#Коэффициенты прямой
a, b = 0.0, 0.0

#Списки для хранения истории точек и прямых
history_x = []
history_y = []
lines = []

def update_line(x_new, y_new):
    global Sx, Sy, Sxx, Sxy, n, a, b
    
    # Сохраняем новую точку
    history_x.append(x_new)
    history_y.append(y_new)
    
    #Обновляем суммы
    n += 1
    Sx += x_new
    Sy += y_new
    Sxx += x_new ** 2
    Sxy += x_new * y_new
    
    #Вычисляем коэффициенты
    if n >= 2:
        denominator = n * Sxx - Sx**2
        if denominator != 0:
            a = (n * Sxy - Sx * Sy) / denominator
            b = (Sy - a * Sx) / n
        else:
            a, b = float('inf'), float('inf')
    
    lines.append((a, b))

#Функция для отрисовки: одно состояние на отдельной панели
def plot_current_state(ax, step):
    ax.scatter(history_x, history_y, color='red', label='Точки данных', zorder=3)

    if n >= 2 and a != float('inf'):
        x_vals = np.linspace(min(history_x) - 1, max(history_x) + 1, 100)
        ax.plot(x_vals, a * x_vals + b, 'b-', label=f'y = {a:.2f}x + {b:.2f}')

    ax.set_title(f'Шаг {step}: точка ({history_x[-1]}, {history_y[-1]})')
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.legend(fontsize=8)
    ax.grid(True)

#Последовательное добавление точек с визуализацией
points = [(1, 2), (2, 3.5), (3, 3.9), (4, 6)]
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
for i, ((x, y), ax) in enumerate(zip(points, axes.ravel()), 1):
    update_line(x, y)
    plot_current_state(ax, i)
    if n >= 2:
        print(f"После точки ({x}, {y}): y = {a:.2f}x + {b:.2f}")
    else:
        print(f"После точки ({x}, {y}): одной точки мало, прямая не определена")

plt.tight_layout()
plt.savefig(OUT_DIR / 'result.png', dpi=120, bbox_inches='tight')
plt.show()

#Предсказание
x_new = 5
print(f"\nПредсказание для x={x_new}: y={a*x_new + b:.2f}")