import numpy as np
from scipy.integrate import quad
from scipy.optimize import minimize
from scipy.stats import multivariate_normal
import matplotlib.pyplot as plt

# Параметры первого кластера (двумерное нормальное распределение)
mu1 = np.array([2.0, 3.0])
sigma1 = np.array([[1.0, 0.3],
                    [0.3, 1.0]])

# Параметры второго кластера
mu2 = np.array([7.0, 8.0])
sigma2 = np.array([[1.5, -0.4],
                    [-0.4, 1.5]])

# Плотность смеси двух распределений с равными весами
def mixture_density(x, y):
    pos = np.array([x, y])
    p1 = multivariate_normal.pdf(pos, mean=mu1, cov=sigma1)
    p2 = multivariate_normal.pdf(pos, mean=mu2, cov=sigma2)
    return 0.5 * p1 + 0.5 * p2

# Градиент плотности смеси (численный)
def grad_density(x, y, h=1e-5):
    dp_dx = (mixture_density(x + h, y) - mixture_density(x - h, y)) / (2 * h)
    dp_dy = (mixture_density(x, y + h) - mixture_density(x, y - h)) / (2 * h)
    return np.array([dp_dx, dp_dy])

# Метрический тензор на поверхности плотности z = f(x, y)
# g_ij = delta_ij + (df/dxi)(df/dxj)
def metric_tensor(x, y):
    g = grad_density(x, y)
    G = np.eye(2) + np.outer(g, g)
    return G

# Параметризация пути через линейную комбинацию с отклонениями
# Путь: gamma(t) = (1-t)*mu1 + t*mu2 + sum(a_k * sin(k*pi*t))
def path_point(t, coeffs_x, coeffs_y):
    x = (1 - t) * mu1[0] + t * mu2[0]
    y = (1 - t) * mu1[1] + t * mu2[1]
    for k, (ax, ay) in enumerate(zip(coeffs_x, coeffs_y), start=1):
        x += ax * np.sin(k * np.pi * t)
        y += ay * np.sin(k * np.pi * t)
    return x, y

# Производная пути по параметру t
def path_derivative(t, coeffs_x, coeffs_y):
    dx = mu2[0] - mu1[0]
    dy = mu2[1] - mu1[1]
    for k, (ax, ay) in enumerate(zip(coeffs_x, coeffs_y), start=1):
        dx += ax * k * np.pi * np.cos(k * np.pi * t)
        dy += ay * k * np.pi * np.cos(k * np.pi * t)
    return dx, dy

# Подынтегральная функция длины пути в метрике поверхности
def integrand(t, coeffs_x, coeffs_y):
    x, y = path_point(t, coeffs_x, coeffs_y)
    dx, dy = path_derivative(t, coeffs_x, coeffs_y)
    G = metric_tensor(x, y)
    v = np.array([dx, dy])
    ds = np.sqrt(v @ G @ v)
    return ds

# Длина пути
def path_length(params, n_basis):
    coeffs_x = params[:n_basis]
    coeffs_y = params[n_basis:]
    length, _ = quad(integrand, 0, 1, args=(coeffs_x, coeffs_y), limit=100)
    return length

# Покоординатный расчет с контролем точности
def compute_geodesic_with_accuracy_control():
    print("=" * 60)
    print("Расчет геодезического расстояния между кластерами")
    print("=" * 60)
    print(f"\nЦентроид 1: {mu1}")
    print(f"Центроид 2: {mu2}")

    # Евклидово расстояние для сравнения
    euclidean = np.linalg.norm(mu2 - mu1)
    print(f"\nЕвклидово расстояние: {euclidean:.6f}")

    # Покоординатный расчет длины по x и по y
    print("\n--- Покоординатный расчет ---")

    # Длина по x-координате
    def integrand_x(t, coeffs_x):
        x = (1 - t) * mu1[0] + t * mu2[0]
        for k, ax in enumerate(coeffs_x, start=1):
            x += ax * np.sin(k * np.pi * t)
        y = (1 - t) * mu1[1] + t * mu2[1]
        dx = mu2[0] - mu1[0]
        for k, ax in enumerate(coeffs_x, start=1):
            dx += ax * k * np.pi * np.cos(k * np.pi * t)
        g = grad_density(x, y)
        return abs(dx) * np.sqrt(1 + g[0]**2)

    # Длина по y-координате
    def integrand_y(t, coeffs_y):
        x = (1 - t) * mu1[0] + t * mu2[0]
        y = (1 - t) * mu1[1] + t * mu2[1]
        for k, ay in enumerate(coeffs_y, start=1):
            y += ay * np.sin(k * np.pi * t)
        dy = mu2[1] - mu1[1]
        for k, ay in enumerate(coeffs_y, start=1):
            dy += ay * k * np.pi * np.cos(k * np.pi * t)
        g = grad_density(x, y)
        return abs(dy) * np.sqrt(1 + g[1]**2)

    # Контроль точности аппроксимации: увеличиваем число базисных функций
    print("\nКонтроль точности (увеличение числа базисных функций):")
    prev_length = None
    best_length = None
    best_params = None
    best_n = None

    for n_basis in range(0, 6):
        x0 = np.zeros(2 * n_basis) if n_basis > 0 else np.array([])

        if n_basis == 0:
            length = path_length(np.array([]), 0)
        else:
            result = minimize(path_length, x0, args=(n_basis,),
                              method='Nelder-Mead',
                              options={'maxiter': 5000, 'xatol': 1e-8, 'fatol': 1e-8})
            length = result.fun
            params = result.x

        if prev_length is not None:
            delta = abs(length - prev_length)
            rel_delta = delta / prev_length * 100
            print(f"  N_basis = {n_basis}: длина = {length:.8f}, "
                  f"изменение = {delta:.2e} ({rel_delta:.4f}%)")

            if rel_delta < 0.01:
                print(f"  -> Точность достигнута при N_basis = {n_basis}")
                best_length = length
                best_n = n_basis
                if n_basis > 0:
                    best_params = params
                break
        else:
            print(f"  N_basis = {n_basis}: длина = {length:.8f} (прямая линия)")

        prev_length = length
        best_length = length
        best_n = n_basis
        if n_basis > 0:
            best_params = params

    print(f"\nГеодезическое расстояние: {best_length:.8f}")
    print(f"Отношение к евклидову: {best_length / euclidean:.6f}")

    return best_length, best_params, best_n

# Визуализация
def visualize(best_params, best_n):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Сетка для построения поверхности плотности
    x_range = np.linspace(-1, 11, 200)
    y_range = np.linspace(0, 12, 200)
    X, Y = np.meshgrid(x_range, y_range)
    Z = np.zeros_like(X)
    for i in range(X.shape[0]):
        for j in range(X.shape[1]):
            Z[i, j] = mixture_density(X[i, j], Y[i, j])

    # Контурный график плотности смеси
    ax1 = axes[0]
    contour = ax1.contourf(X, Y, Z, levels=30, cmap='viridis')
    plt.colorbar(contour, ax=ax1, label='Плотность смеси')

    # Построение прямой и геодезической линий
    t_vals = np.linspace(0, 1, 200)

    # Прямая линия
    straight_x = [(1 - t) * mu1[0] + t * mu2[0] for t in t_vals]
    straight_y = [(1 - t) * mu1[1] + t * mu2[1] for t in t_vals]
    ax1.plot(straight_x, straight_y, 'w--', linewidth=2, label='Прямая линия')

    # Геодезическая
    if best_params is not None and best_n > 0:
        coeffs_x = best_params[:best_n]
        coeffs_y = best_params[best_n:]
        geo_x = [path_point(t, coeffs_x, coeffs_y)[0] for t in t_vals]
        geo_y = [path_point(t, coeffs_x, coeffs_y)[1] for t in t_vals]
        ax1.plot(geo_x, geo_y, 'r-', linewidth=2, label='Геодезическая')

    # Центроиды
    ax1.plot(*mu1, 'wo', markersize=10, markeredgecolor='black', label='Центроид 1')
    ax1.plot(*mu2, 'ws', markersize=10, markeredgecolor='black', label='Центроид 2')
    ax1.set_xlabel('x')
    ax1.set_ylabel('y')
    ax1.set_title('Плотность смеси и геодезическая линия')
    ax1.legend(fontsize=8)

    # 3D-поверхность
    ax2 = fig.add_subplot(122, projection='3d')
    axes[1].remove()
    ax2.plot_surface(X, Y, Z, cmap='viridis', alpha=0.7, edgecolor='none')

    # Геодезическая на поверхности
    if best_params is not None and best_n > 0:
        geo_z = [mixture_density(gx, gy) for gx, gy in zip(geo_x, geo_y)]
        ax2.plot(geo_x, geo_y, geo_z, 'r-', linewidth=2, label='Геодезическая')

    str_z = [mixture_density(sx, sy) for sx, sy in zip(straight_x, straight_y)]
    ax2.plot(straight_x, straight_y, str_z, 'w--', linewidth=2, label='Прямая')

    ax2.set_xlabel('x')
    ax2.set_ylabel('y')
    ax2.set_zlabel('Плотность')
    ax2.set_title('Поверхность плотности смеси')

    plt.tight_layout()
    plt.savefig('task1_result.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("\nГрафик сохранен: task1_result.png")


if __name__ == "__main__":
    best_length, best_params, best_n = compute_geodesic_with_accuracy_control()
    visualize(best_params, best_n)
