"""Геодезическое расстояние между двумя кластерами по поверхности плотности их смеси

Поверхность задаётся как z = SCALE * p(x, y), где p(x, y) это плотность смеси двух
нормальных распределений. Длина пути считается в трёхмерном пространстве (x, y, z),
а геодезическая ищется как кратчайший путь между центроидами на этой поверхности
"""
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from scipy.stats import multivariate_normal

OUT_DIR = Path(__file__).resolve().parent

# Параметры кластеров
mu1 = np.array([2.0, 3.0])
sigma1 = np.array([[1.0, 0.3],
                   [0.3, 1.0]])
mu2 = np.array([7.0, 8.0])
sigma2 = np.array([[1.5, -0.4],
                   [-0.4, 1.5]])

# Высота пика поверхности в единицах координат x, y.
# Сама плотность имеет порядок 0.1, и без масштабирования поверхность почти плоская:
# геодезическая совпадает с прямой, а задача вырождается в евклидово расстояние
PEAK_HEIGHT = 3.0


def mixture_density(x, y):
    pos = np.stack([x, y], axis=-1)
    return 0.5 * multivariate_normal.pdf(pos, mu1, sigma1) + 0.5 * multivariate_normal.pdf(pos, mu2, sigma2)


SCALE = PEAK_HEIGHT / mixture_density(*mu1)

# Путь: прямая между центроидами + отклонения по нормали к ней.
# Отклонения только по нормали, чтобы оптимизатор не тратил силы на
# перепараметризацию того же самого отрезка
direction = (mu2 - mu1) / np.linalg.norm(mu2 - mu1)
normal = np.array([-direction[1], direction[0]])


def path_points(coeffs, t):
    base = (1 - t)[:, None] * mu1 + t[:, None] * mu2
    shift = np.zeros_like(t)
    for k, c in enumerate(coeffs, start=1):
        shift += c * np.sin(k * np.pi * t)
    return base + shift[:, None] * normal


def path_length(coeffs, n_grid):
    t = np.linspace(0, 1, n_grid)
    xy = path_points(coeffs, t)
    z = SCALE * mixture_density(xy[:, 0], xy[:, 1])
    seg = np.sqrt(np.diff(xy[:, 0]) ** 2 + np.diff(xy[:, 1]) ** 2 + np.diff(z) ** 2)
    return seg.sum()


def find_geodesic(n_basis, n_grid, restarts=5):
    if n_basis == 0:
        return path_length([], n_grid), np.array([])
    best = None
    for seed in range(restarts):
        x0 = np.zeros(n_basis) if seed == 0 else np.random.default_rng(seed).normal(0, 1.5, n_basis)
        res = minimize(path_length, x0, args=(n_grid,), method="Powell")
        if best is None or res.fun < best.fun:
            best = res
    return best.fun, best.x


def main():
    euclid = np.linalg.norm(mu2 - mu1)
    print(f"Евклидово расстояние между центроидами: {euclid:.4f}")
    print(f"Высота пика поверхности: {PEAK_HEIGHT}\n")

    # Контроль точности: сгущаем сетку и добавляем базисные функции,
    # пока длина не перестанет меняться
    print("Контроль точности")
    prev, coeffs = None, np.array([])
    for n_basis, n_grid in [(0, 200), (1, 400), (2, 800), (3, 1600), (4, 3200)]:
        length, c = find_geodesic(n_basis, n_grid)
        note = "" if prev is None else f"  изменение {abs(length - prev) / prev * 100:.4f}%"
        print(f"  базисных функций {n_basis}, точек {n_grid}: длина {length:.6f}{note}")
        if prev is not None and abs(length - prev) / prev < 1e-4:
            coeffs = c
            break
        prev, coeffs = length, c

    straight = path_length([], 3200)
    print(f"\nДлина прямой по поверхности: {straight:.4f}")
    print(f"Геодезическое расстояние:    {length:.4f}")
    print(f"Отношение к евклидову:       {length / euclid:.4f}")

    plot(coeffs)


def plot(coeffs):
    xs = np.linspace(-1, 11, 200)
    ys = np.linspace(0, 12, 200)
    X, Y = np.meshgrid(xs, ys)
    Z = SCALE * mixture_density(X, Y)

    t = np.linspace(0, 1, 300)
    geo = path_points(coeffs, t)
    line = path_points([], t)

    fig = plt.figure(figsize=(14, 6))
    ax1 = fig.add_subplot(121)
    cf = ax1.contourf(X, Y, Z, levels=30, cmap="viridis")
    fig.colorbar(cf, ax=ax1, label="Высота поверхности")
    ax1.plot(line[:, 0], line[:, 1], "w--", lw=2, label="Прямая")
    ax1.plot(geo[:, 0], geo[:, 1], "r-", lw=2, label="Геодезическая")
    ax1.plot(*mu1, "wo", ms=9, mec="k")
    ax1.plot(*mu2, "ws", ms=9, mec="k")
    ax1.set_title("Плотность смеси и путь между центроидами")
    ax1.set_xlabel("x")
    ax1.set_ylabel("y")
    ax1.legend(fontsize=8)

    ax2 = fig.add_subplot(122, projection="3d")
    ax2.plot_surface(X, Y, Z, cmap="viridis", alpha=0.7, edgecolor="none")
    ax2.plot(geo[:, 0], geo[:, 1], SCALE * mixture_density(geo[:, 0], geo[:, 1]), "r-", lw=2)
    ax2.set_title("Поверхность плотности")
    ax2.set_xlabel("x")
    ax2.set_ylabel("y")

    plt.tight_layout()
    plt.savefig(OUT_DIR / "result.png", dpi=120, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    main()
