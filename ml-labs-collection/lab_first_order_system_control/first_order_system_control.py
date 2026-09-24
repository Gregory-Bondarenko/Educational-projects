from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

OUT_DIR = Path(__file__).resolve().parent

# Параметры апериодического звена первого порядка
# Передаточная функция: W(s) = K / (T*s + 1)
K = 2.0        # Коэффициент усиления
T = 3.0        # Постоянная времени
y0 = 0.0       # Начальное значение выходной переменной
d = 1.0        # Величина скачкообразного возмущения

# Параметры пропорционального регулятора
Kp = 5.0       # Коэффициент пропорционального регулятора
y_ref = 0.0    # Уставка (желаемое значение)

# Параметры моделирования
dt = 0.01      # Шаг интегрирования
t_end = 30.0   # Время моделирования
t = np.arange(0, t_end, dt)

# Моделирование методом Эйлера

# Случай 1: без управления (только возмущение)
def simulate_no_control():
    y = np.zeros(len(t))
    y[0] = y0
    for i in range(1, len(t)):
        # dy/dt = (-y + K*d) / T
        dydt = (-y[i-1] + K * d) / T
        y[i] = y[i-1] + dydt * dt
    return y

# Случай 2: с пропорциональным управлением
def simulate_with_p_control():
    y = np.zeros(len(t))
    u = np.zeros(len(t))
    y[0] = y0

    for i in range(1, len(t)):
        # Ошибка регулирования
        error = y_ref - y[i-1]
        # Управляющее воздействие
        u[i] = Kp * error
        # dy/dt = (-y + K*(u + d)) / T
        dydt = (-y[i-1] + K * (u[i] + d)) / T
        y[i] = y[i-1] + dydt * dt

    return y, u

# Аналитические решения для проверки

# Без управления: y(t) = K*d * (1 - exp(-t/T))
def analytical_no_control():
    return K * d * (1 - np.exp(-t / T))

# С П-регулятором: y_ss = K*d / (1 + K*Kp)
def analytical_with_control():
    T_eff = T / (1 + K * Kp)
    K_eff = K * d / (1 + K * Kp)
    return K_eff * (1 - np.exp(-t / T_eff))

# Расчет
print("=" * 60)
print("Динамика апериодического звена первого порядка")
print("=" * 60)
print(f"\nПараметры звена: K = {K}, T = {T}")
print(f"Возмущение: d = {d}")
print(f"Коэффициент П-регулятора: Kp = {Kp}")
print(f"Уставка: y_ref = {y_ref}")

y_no_ctrl = simulate_no_control()
y_with_ctrl, u_ctrl = simulate_with_p_control()

# Установившиеся значения
y_ss_no_ctrl = K * d
y_ss_with_ctrl = K * d / (1 + K * Kp)
steady_error = y_ref - y_ss_with_ctrl

print(f"\n--- Без управления ---")
print(f"Установившееся значение: y_ss = {y_ss_no_ctrl:.4f}")

print(f"\n--- С П-регулятором ---")
print(f"Установившееся значение: y_ss = {y_ss_with_ctrl:.4f}")
print(f"Стационарная ошибка управления: e_ss = {abs(steady_error):.4f}")
print(f"(Ошибка обусловлена природой пропорционального регулятора,")
print(f" который не может полностью компенсировать возмущение)")

# Визуализация
fig, axes = plt.subplots(2, 1, figsize=(12, 8))

# Верхний график: выходная переменная
ax1 = axes[0]
ax1.plot(t, y_no_ctrl, 'b-', linewidth=2, label='Без управления')
ax1.plot(t, y_with_ctrl, 'r-', linewidth=2, label=f'С П-регулятором (Kp={Kp})')
ax1.axhline(y=y_ss_no_ctrl, color='b', linestyle='--', alpha=0.5,
            label=f'y_ss без упр. = {y_ss_no_ctrl:.2f}')
ax1.axhline(y=y_ss_with_ctrl, color='r', linestyle='--', alpha=0.5,
            label=f'y_ss с П-рег. = {y_ss_with_ctrl:.4f}')
ax1.axhline(y=y_ref, color='g', linestyle=':', alpha=0.7, label=f'Уставка = {y_ref}')

# Отметка стационарной ошибки
ax1.annotate('', xy=(t_end * 0.85, y_ref), xytext=(t_end * 0.85, y_ss_with_ctrl),
             arrowprops=dict(arrowstyle='<->', color='darkred', lw=1.5))
ax1.text(t_end * 0.87, (y_ref + y_ss_with_ctrl) / 2,
         f'e_ss = {abs(steady_error):.4f}',
         fontsize=10, color='darkred', va='center')

ax1.set_xlabel('Время, с')
ax1.set_ylabel('Выход y(t)')
ax1.set_title('Реакция апериодического звена на скачкообразное возмущение')
ax1.legend(loc='right', fontsize=8)
ax1.grid(True, alpha=0.3)

# Нижний график: управляющее воздействие
ax2 = axes[1]
ax2.plot(t, u_ctrl, 'r-', linewidth=2, label='Управление u(t)')
ax2.axhline(y=0, color='k', linestyle='-', alpha=0.3)
u_ss = Kp * (y_ref - y_ss_with_ctrl)
ax2.axhline(y=u_ss, color='r', linestyle='--', alpha=0.5,
            label=f'u_ss = {u_ss:.4f}')
ax2.set_xlabel('Время, с')
ax2.set_ylabel('Управление u(t)')
ax2.set_title('Управляющее воздействие П-регулятора')
ax2.legend(fontsize=8)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(OUT_DIR / 'result.png', dpi=120, bbox_inches='tight')
plt.show()
print("\nГрафик сохранён: result.png")
