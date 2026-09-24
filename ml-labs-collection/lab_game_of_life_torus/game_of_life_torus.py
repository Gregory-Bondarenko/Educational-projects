from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

OUT_DIR = Path(__file__).resolve().parent

# Параметры клеточного автомата
GRID_SIZE = 100
MAX_STEPS = 1000

# Ходы для визуализации (задаются заранее)
DISPLAY_STEPS = [0, 10, 50, 100, 200]

# Инициализация случайного начального состояния
def init_grid(size, fill_ratio=0.3):
    np.random.seed(42)
    grid = (np.random.random((size, size)) < fill_ratio).astype(int)
    return grid

# Подсчет соседей на торе (периодические граничные условия)
def count_neighbors(grid):
    size = grid.shape[0]
    neighbors = np.zeros_like(grid)
    for di in [-1, 0, 1]:
        for dj in [-1, 0, 1]:
            if di == 0 and dj == 0:
                continue
            # Периодические граничные условия реализуются через np.roll
            neighbors += np.roll(np.roll(grid, di, axis=0), dj, axis=1)
    return neighbors

# Один шаг игры "Жизнь"
def step(grid):
    neighbors = count_neighbors(grid)
    # Правила: живая клетка выживает при 2 или 3 соседях,
    # мертвая оживает при ровно 3 соседях
    new_grid = np.zeros_like(grid)
    new_grid[(grid == 1) & ((neighbors == 2) | (neighbors == 3))] = 1
    new_grid[(grid == 0) & (neighbors == 3)] = 1
    return new_grid

# Проверка устойчивого состояния
def is_stable(grid, prev_grid, prev_prev_grid):
    # Проверяем неподвижную точку (состояние не меняется)
    if np.array_equal(grid, prev_grid):
        return True, "неподвижная точка"
    # Проверяем цикл периода 2 (осцилляторы)
    if prev_prev_grid is not None and np.array_equal(grid, prev_prev_grid):
        return True, "цикл периода 2"
    return False, ""

# Основной цикл моделирования
def run_simulation():
    print("=" * 60)
    print("Игра 'Жизнь' на торе 100x100")
    print("=" * 60)

    grid = init_grid(GRID_SIZE)
    print(f"Начальное число живых клеток: {np.sum(grid)}")
    print(f"Максимальное количество ходов: {MAX_STEPS}")
    print(f"Ходы для визуализации: {DISPLAY_STEPS}")

    # Сохраняем состояния на заданных ходах
    saved_states = {}
    if 0 in DISPLAY_STEPS:
        saved_states[0] = grid.copy()

    prev_grid = None
    prev_prev_grid = None
    final_step = MAX_STEPS

    for t in range(1, MAX_STEPS + 1):
        prev_prev_grid = prev_grid
        prev_grid = grid.copy()
        grid = step(grid)

        # Сохраняем состояние для визуализации
        if t in DISPLAY_STEPS:
            saved_states[t] = grid.copy()

        # Проверка на устойчивое состояние
        stable, reason = is_stable(grid, prev_grid, prev_prev_grid)
        if stable:
            print(f"\nУстойчивое состояние достигнуто на ходу {t}: {reason}")
            final_step = t
            # Сохраняем финальное состояние
            saved_states[t] = grid.copy()
            break

        # Вывод промежуточной статистики
        if t % 50 == 0:
            alive = np.sum(grid)
            print(f"  Ход {t}: живых клеток = {alive}")

    if final_step == MAX_STEPS:
        print(f"\nМаксимальное число ходов ({MAX_STEPS}) достигнуто.")

    print(f"Итоговое число живых клеток: {np.sum(grid)}")

    return saved_states, final_step

# Визуализация состояний на заданных ходах
def visualize(saved_states):
    steps_to_show = sorted(saved_states.keys())[:5]
    n_plots = len(steps_to_show)

    fig, axes = plt.subplots(1, n_plots, figsize=(4 * n_plots, 4))
    if n_plots == 1:
        axes = [axes]

    for ax, t in zip(axes, steps_to_show):
        ax.imshow(saved_states[t], cmap='binary', interpolation='nearest')
        alive = np.sum(saved_states[t])
        ax.set_title(f'Ход {t}\n(живых: {alive})', fontsize=10)
        ax.set_xticks([0, 25, 50, 75, 99])
        ax.set_yticks([0, 25, 50, 75, 99])
        ax.tick_params(labelsize=7)

    fig.suptitle("Игра 'Жизнь' на торе 100×100", fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(OUT_DIR / 'result.png', dpi=120, bbox_inches='tight')
    plt.show()
    print("\nГрафик сохранён: result.png")


if __name__ == "__main__":
    saved_states, final_step = run_simulation()
    visualize(saved_states)
