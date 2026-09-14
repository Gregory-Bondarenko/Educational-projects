#Импорт библиотек
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint
from scipy.optimize import curve_fit

#Задача: построить фазовый портрет в 2n-мерном пространстве параметров
#и их скоростей на основе набора данных. Аппроксимировать фазовые траектории
#аналитическими функциями с оценкой невязки.
#
#Модельная система: связанные осцилляторы (n = 2, пространство 4-мерное)
#x1'' + b1*x1' + w1^2*x1 + k*(x1 - x2) = 0
#x2'' + b2*x2' + w2^2*x2 + k*(x2 - x1) = 0
#
#Параметры и скорости: (x1, x2, x1', x2') — 2n = 4 измерения

#Параметры системы
W1 = 1.0       # собственная частота первого осциллятора
W2 = 1.3       # собственная частота второго
B1 = 0.1       # демпфирование первого
B2 = 0.15      # демпфирование второго
K_COUPLING = 0.3  # коэффициент связи

#Правая часть ОДУ (4-мерная система первого порядка)
#Состояние: [x1, x2, v1, v2], где v = dx/dt
def system(state, t):
    x1, x2, v1, v2 = state
    dx1 = v1
    dx2 = v2
    dv1 = -B1*v1 - W1**2*x1 - K_COUPLING*(x1 - x2)
    dv2 = -B2*v2 - W2**2*x2 - K_COUPLING*(x2 - x1)
    return [dx1, dx2, dv1, dv2]

#Генерация набора данных: траектории из различных начальных условий
def generate_data():
    t_span = np.linspace(0, 40, 2000)
    initial_conditions = [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [1.0, 1.0, 0.0, 0.0],
        [1.0, -1.0, 0.0, 0.0],
        [0.5, 0.5, 0.5, -0.5],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
        [1.5, -0.5, -0.3, 0.8],
    ]
    trajectories = []
    for ic in initial_conditions:
        sol = odeint(system, ic, t_span)
        trajectories.append((t_span, sol))
    return trajectories

#Аналитическая аппроксимация фазовой траектории.
#Для затухающего осциллятора фазовая траектория на плоскости (x, v) аппроксимируется
#логарифмической спиралью: x(t) = A*exp(-α*t)*cos(ωt + φ), v(t) = dx/dt
#
#Модель аппроксимации для каждой координаты:
#f(t) = A * exp(-alpha * t) * cos(omega * t + phi) + C
def approx_model(t, A, alpha, omega, phi, C):
    return A * np.exp(-alpha * t) * np.cos(omega * t + phi) + C

#Аппроксимация одной траектории по одной координате
def fit_trajectory(t, data):
    #Начальные приближения
    A0 = np.max(np.abs(data))
    alpha0 = 0.1
    omega0 = 1.0
    phi0 = 0.0
    C0 = np.mean(data[-100:])

    try:
        popt, _ = curve_fit(approx_model, t, data,
                               p0=[A0, alpha0, omega0, phi0, C0],
                               maxfev=10000)
        fitted = approx_model(t, *popt)
        residual = np.sqrt(np.mean((data - fitted)**2))
        return popt, fitted, residual
    except RuntimeError:
        return None, None, np.inf

def main():
    print("=" * 60)
    print("Фазовый портрет в 2n-мерном пространстве по данным")
    print("=" * 60)
    print(f"\nМодельная система: два связанных осциллятора (n = 2)")
    print(f"Пространство фазового портрета: 4-мерное (x1, x2, v1, v2)")
    print(f"ω₁ = {W1}, ω₂ = {W2}, b₁ = {B1}, b₂ = {B2}, k = {K_COUPLING}")

    trajectories = generate_data()
    print(f"Сгенерировано {len(trajectories)} траекторий")

    #Аппроксимация траекторий
    print("\n--- Аппроксимация траекторий ---")
    print("Модель: f(t) = A·exp(−α·t)·cos(ω·t + φ) + C")
    print()

    fit_results = []
    for idx, (t, sol) in enumerate(trajectories):
        residuals = []
        fitted_curves = []
        for dim in range(4):
            popt, fitted, res = fit_trajectory(t, sol[:, dim])
            residuals.append(res)
            fitted_curves.append(fitted)
        fit_results.append((residuals, fitted_curves))
        labels = ['x1', 'x2', 'v1', 'v2']
        res_str = ', '.join([f'{labels[d]}: {residuals[d]:.4f}' for d in range(4)])
        print(f"  Траектория {idx+1}: невязки (RMSE) — {res_str}")

    #Средняя невязка по всем траекториям и координатам
    all_res = [r for res_list, _ in fit_results for r in res_list if r < np.inf]
    print(f"\nСредняя невязка (RMSE): {np.mean(all_res):.6f}")
    print(f"Максимальная невязка: {np.max(all_res):.6f}")

    #Визуализация
    fig = plt.figure(figsize=(16, 12))

    #1. Проекции фазового портрета на 2D-плоскости (6 комбинаций из 4 координат)
    coord_labels = ['$x_1$', '$x_2$', "$x'_1$", "$x'_2$"]
    pairs = [(0, 2), (1, 3), (0, 1), (2, 3), (0, 3), (1, 2)]  # (x1,v1), (x2,v2), etc.
    pair_titles = ['$(x_1, x\'_1)$', '$(x_2, x\'_2)$', '$(x_1, x_2)$',
                   "$(x'_1, x'_2)$", "$(x_1, x'_2)$", "$(x_2, x'_1)$"]

    gs = fig.add_gridspec(3, 3, hspace=0.4, wspace=0.35)

    for p_idx, (d1, d2) in enumerate(pairs):
        ax = fig.add_subplot(gs[p_idx // 3, p_idx % 3])
        for t, sol in trajectories:
            ax.plot(sol[:, d1], sol[:, d2], linewidth=0.7, alpha=0.7)
        ax.set_xlabel(coord_labels[d1], fontsize=10)
        ax.set_ylabel(coord_labels[d2], fontsize=10)
        ax.set_title(f'Проекция {pair_titles[p_idx]}', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal' if d1 < 2 and d2 >= 2 else 'auto')

    #2. Пример аппроксимации: первая траектория, координата x1
    ax_fit = fig.add_subplot(gs[2, 0:2])
    t0, sol0 = trajectories[0]
    ax_fit.plot(t0, sol0[:, 0], 'b-', linewidth=1.5, label='Данные $x_1(t)$')
    if fit_results[0][1][0] is not None:
        ax_fit.plot(t0, fit_results[0][1][0], 'r--', linewidth=1.2,
                    label=f'Аппроксимация (RMSE={fit_results[0][0][0]:.4f})')
    ax_fit.set_xlabel('Время t', fontsize=10)
    ax_fit.set_ylabel('$x_1(t)$', fontsize=10)
    ax_fit.set_title('Аппроксимация фазовой траектории (траектория 1, координата $x_1$)', fontsize=10)
    ax_fit.legend(fontsize=9)
    ax_fit.grid(True, alpha=0.3)

    #3. Невязки по всем траекториям
    ax_res = fig.add_subplot(gs[2, 2])
    res_matrix = np.array([r[0] for r in fit_results])
    labels_short = ['x1', 'x2', 'v1', 'v2']
    x_pos = np.arange(len(trajectories))
    width = 0.2
    for d in range(4):
        ax_res.bar(x_pos + d*width, res_matrix[:, d], width, label=labels_short[d])
    ax_res.set_xlabel('Траектория', fontsize=10)
    ax_res.set_ylabel('RMSE', fontsize=10)
    ax_res.set_title('Невязки аппроксимации', fontsize=10)
    ax_res.set_xticks(x_pos + 1.5*width)
    ax_res.set_xticklabels([str(i+1) for i in range(len(trajectories))], fontsize=8)
    ax_res.legend(fontsize=8)
    ax_res.grid(True, alpha=0.3, axis='y')

    fig.suptitle("Фазовый портрет системы связанных осцилляторов\n"
                 "в 4-мерном пространстве (x₁, x₂, x'₁, x'₂)",
                 fontsize=13, fontweight='bold')
    plt.savefig('tz5_result.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("\nГрафик сохранён: tz5_result.png")

if __name__ == "__main__":
    main()
