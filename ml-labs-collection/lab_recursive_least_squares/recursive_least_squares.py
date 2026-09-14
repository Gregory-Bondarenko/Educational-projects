import matplotlib.pyplot as plt
import numpy as np

Sx = 0.0   #сумма всех x
Sy = 0.0  #сумма всех y
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

#Функция для отрисовки
def plot_current_state(step):
    plt.figure(figsize=(10, 5))
    
    # Отрисовываем все полученные точки
    plt.scatter(history_x, history_y, color='red', label='Точки данных')
    
    # Отрисовываем текущую аппроксимирующую прямую
    if n >= 2 and a != float('inf'):
        x_min, x_max = min(history_x), max(history_x)
        x_vals = np.linspace(x_min-1, x_max+1, 100)
        y_vals = a * x_vals + b
        plt.plot(x_vals, y_vals, 'b-', label=f'y = {a:.2f}x + {b:.2f}')
    
    plt.title(f'Шаг {step}: Точка ({history_x[-1]}, {history_y[-1]})')
    plt.xlabel('x')
    plt.ylabel('y')
    plt.legend()
    plt.grid(True)
    plt.show()

#Последовательное добавление точек с визуализацией
points = [(1, 2), (2, 3.5), (3, 3.9), (4, 6)]
for i, (x, y) in enumerate(points, 1):
    update_line(x, y)
    plot_current_state(i)
    print(f"После точки ({x}, {y}): y = {a:.2f}x + {b:.2f}")

#Предсказание
x_new = 5
print(f"\nПредсказание для x={x_new}: y={a*x_new + b:.2f}")