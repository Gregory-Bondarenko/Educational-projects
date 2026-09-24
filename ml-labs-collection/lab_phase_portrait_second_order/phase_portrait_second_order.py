from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint

OUT_DIR = Path(__file__).resolve().parent

# Динамическая система второго порядка
# x'' + 2*zeta*omega*x' + omega^2*x = 0
# В переменных состояния: x1 = x, x2 = x' (скорость)
# dx1/dt = x2
# dx2/dt = -omega^2 * x1 - 2*zeta*omega * x2

# Параметры системы
omega = 1.0      # Собственная частота
zeta = 0.3       # Коэффициент демпфирования (< 1 - колебательный режим)

# Правые части системы ОДУ
def system(state, t):
    x1, x2 = state
    dx1 = x2
    dx2 = -omega**2 * x1 - 2 * zeta * omega * x2
    return [dx1, dx2]

# Наклон фазовых траекторий dy/dx = f2/f1
def phase_slope(x1, x2):
    dx1 = x2
    dx2 = -omega**2 * x1 - 2 * zeta * omega * x2
    if abs(dx1) < 1e-10:
        return np.inf
    return dx2 / dx1

# Построение фазового портрета
def build_phase_portrait():
    print("=" * 60)
    print("Фазовый портрет динамической системы второго порядка")
    print("=" * 60)
    print(f"\nУравнение: x'' + {2*zeta*omega:.1f}*x' + {omega**2:.1f}*x = 0")
    print(f"omega = {omega}, zeta = {zeta}")
    print(f"Тип системы: {'колебательная' if zeta < 1 else 'апериодическая'}")

    fig, ax = plt.subplots(figsize=(10, 8))

    # Построение фазовых траекторий из разных начальных условий
    t_span = np.linspace(0, 30, 3000)

    # Набор начальных условий
    initial_conditions = []
    for r in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
        for angle in np.linspace(0, 2 * np.pi, 12, endpoint=False):
            x0 = r * np.cos(angle)
            v0 = r * np.sin(angle)
            initial_conditions.append([x0, v0])

    # Интегрирование и построение траекторий
    for ic in initial_conditions:
        sol = odeint(system, ic, t_span)
        ax.plot(sol[:, 0], sol[:, 1], 'b-', linewidth=0.5, alpha=0.6)

    # Поле направлений
    x1_range = np.linspace(-3.5, 3.5, 20)
    x2_range = np.linspace(-3.5, 3.5, 20)
    X1, X2 = np.meshgrid(x1_range, x2_range)
    DX1 = X2
    DX2 = -omega**2 * X1 - 2 * zeta * omega * X2
    # Нормировка стрелок
    M = np.sqrt(DX1**2 + DX2**2)
    M[M == 0] = 1
    ax.quiver(X1, X2, DX1/M, DX2/M, color='gray', alpha=0.3, scale=30)

    # Изоклины - линии, на которых наклон траекторий dy/dx = const
    # dy/dx = (-omega^2 * x - 2*zeta*omega * y) / y = k
    # => y * k = -omega^2 * x - 2*zeta*omega * y
    # => y * (k + 2*zeta*omega) = -omega^2 * x
    # => y = -omega^2 * x / (k + 2*zeta*omega)

    x_iso = np.linspace(-3.5, 3.5, 300)
    slopes = [0, 1, -1, 0.5, -0.5]  # Углы наклона изоклин
    colors_iso = ['red', 'green', 'orange', 'purple', 'cyan']
    labels_iso = ['k = 0 (горизонтальные)',
                  'k = 1 (45°)',
                  'k = -1 (-45°)',
                  'k = 0.5 (~27°)',
                  'k = -0.5 (~-27°)']

    print("\nИзоклины:")
    for k, color, label in zip(slopes, colors_iso, labels_iso):
        denom = k + 2 * zeta * omega
        if abs(denom) > 1e-10:
            y_iso = -omega**2 * x_iso / denom
            mask = (np.abs(y_iso) < 4.0)
            ax.plot(x_iso[mask], y_iso[mask], color=color, linewidth=2,
                    linestyle='--', label=f'Изоклина {label}')
            print(f"  {label}: y = {-omega**2/denom:.3f} * x")

    # Изоклина dy/dx = inf (вертикальные касательные) - это ось x2 = 0
    ax.axhline(y=0, color='brown', linewidth=2, linestyle='--',
               label='Изоклина k = ∞ (вертикальные)', alpha=0.7)
    print(f"  k = ∞ (вертикальные): y = 0")

    # Особая точка
    ax.plot(0, 0, 'ko', markersize=8, zorder=5)
    ax.annotate('Устойчивый фокус\n(0, 0)', xy=(0, 0), xytext=(0.5, -1.5),
                fontsize=10, arrowprops=dict(arrowstyle='->', color='black'),
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    ax.set_xlabel("x (значение параметра)", fontsize=12)
    ax.set_ylabel("x' (скорость изменения)", fontsize=12)
    ax.set_title(f"Фазовый портрет: x'' + {2*zeta*omega:.1f}x' + {omega**2:.1f}x = 0\n"
                 f"(ω = {omega}, ζ = {zeta}, устойчивый фокус)", fontsize=13)
    ax.set_xlim(-3.5, 3.5)
    ax.set_ylim(-3.5, 3.5)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper left', fontsize=8, framealpha=0.9)

    plt.tight_layout()
    plt.savefig(OUT_DIR / 'result.png', dpi=120, bbox_inches='tight')
    plt.show()
    print("\nГрафик сохранён: result.png")


if __name__ == "__main__":
    build_phase_portrait()
