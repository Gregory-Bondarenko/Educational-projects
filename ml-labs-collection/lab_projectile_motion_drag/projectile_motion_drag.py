from pathlib import Path
import numpy as np
import math
import matplotlib.pyplot as plt

OUT_DIR = Path(__file__).resolve().parent

#Исходные данные
v0 = 50      #м/с  начальная скорость
h = 10       #м  высота старта
m = 0.1      #кг  масса стрелы
c = 0.05     #кг/с  сопротивление воздуха
g = 9.81     #м/с²  ускорение свободного падения

k = c / m    #коэффициент k = c/m

#Массив углов
angles = np.linspace(1, 89, 200) * math.pi / 180  #в радианах
ranges = []  #дальности
times = []   #времена полёта

#Перебор углов
for alpha in angles:
    vx0 = v0 * math.cos(alpha)
    vy0 = v0 * math.sin(alpha)

    #Время полёта T (y(T) = 0)
    t = 0
    dt = 0.01
    y = h
    while y > 0:
        t += dt
        if k == 0:
            y = h + vy0 * t - 0.5 * g * t**2
        else:
            y = h + (vy0 + g / k) * (1 - math.exp(-k * t)) / k - g * t / k
        if t > 100:
            break

    #Дальность
    if k == 0:
        x = vx0 * t
    else:
        x = vx0 * (1 - math.exp(-k * t)) / k

    ranges.append(x)
    times.append(t)

#Оптимальный угол и дальность
ranges = np.array(ranges)
idx = np.argmax(ranges)
alpha_opt = angles[idx] * 180 / math.pi
L_opt = ranges[idx]

print(f"Оптимальный угол: {alpha_opt:.2f}°")
print(f"Максимальная дальность: {L_opt:.2f} м")

#График зависимости дальности от угла
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
plt.sca(ax1)
plt.plot(angles * 180 / math.pi, ranges)
plt.axvline(alpha_opt, color='r', linestyle='--', label=f'α*={alpha_opt:.2f}°')
plt.title("Дальность полёта L(α)")
plt.xlabel("Угол выстрела, °")
plt.ylabel("Дальность, м")
plt.grid(True)
plt.legend()

#Траектория при оптимальном угле
alpha = angles[idx]
vx0 = v0 * math.cos(alpha)
vy0 = v0 * math.sin(alpha)
t_max = times[idx]
t = np.linspace(0, t_max, 300)

if k == 0:
    x = vx0 * t
    y = h + vy0 * t - 0.5 * g * t**2
else:
    x = vx0 * (1 - np.exp(-k * t)) / k
    y = h + (vy0 + g / k) * (1 - np.exp(-k * t)) / k - g * t / k

plt.sca(ax2)
plt.plot(x, y)
plt.title(f"Траектория стрелы (α={alpha_opt:.2f}°)")
plt.xlabel("x, м")
plt.ylabel("y, м")
plt.grid(True)
plt.ylim(bottom=0)
plt.tight_layout()
plt.savefig(OUT_DIR / 'result.png', dpi=120, bbox_inches='tight')
plt.show()