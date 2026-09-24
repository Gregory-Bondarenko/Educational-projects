from pathlib import Path
#Импорт библиотек
import numpy as np
import matplotlib.pyplot as plt

OUT_DIR = Path(__file__).resolve().parent

#Параметры клеточного автомата
GRID_SIZE = 100
MAX_STEPS = 200
DISPLAY_STEPS = [0, 10, 50, 100, 200]

#Множество состояний клетки: {0, 1, 2, 3}
#Закон сохранения: суммарное "количество вещества" S = ΣΣ grid[i,j] сохраняется.
#Состояние "0" - пустая клетка. Состояния 1, 2, 3 - различные уровни заполнения.
NUM_STATES = 4

#Окрестность фон Неймана (4 соседа: верх, низ, лево, право)
NEIGHBORS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

#Граничные условия: отсутствующие клетки - в состоянии "0".
#Реализуется через дополнение массива нулями (padding).

#Инициализация: детерминированная конфигурация с известной суммой
def init_grid():
    grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=int)
    #Квадратный блок заполненных клеток в центре
    grid[40:60, 40:60] = 2
    #Несколько клеток с высоким значением
    grid[50, 50] = 3
    grid[45, 55] = 3
    grid[55, 45] = 3
    return grid

#Правило перехода с сохранением суммы.
#Идея: перераспределение «вещества» между соседними клетками.
#Для каждой клетки (i,j) вычисляем среднее значение по ней и её соседям,
#затем округляем так, чтобы суммарное количество сохранялось.
#
#Конкретное правило:
#1) Для каждой клетки считаем сумму в окрестности (с учётом граничных нулей)
#2) Если клетка содержит больше среднего по окрестности и хотя бы один сосед
#   содержит меньше среднего - передаём 1 единицу «вещества» от клетки к
#   наименее заполненному соседу.
#3) Это гарантирует: каждая элементарная операция - пара (+1, -1), суммарно 0.
def step(grid, t):
    N = GRID_SIZE
    new_grid = grid.copy()
    #Порядок обхода клеток случайный, но воспроизводимый: seed зависит от номера хода
    rng = np.random.default_rng(seed=t)
    indices = list(np.ndindex(N, N))
    rng.shuffle(indices)
    
    for i, j in indices:
        if new_grid[i, j] <= 0:
            continue
        #Собираем значения соседей (граничные = 0)
        neighbor_vals = []
        neighbor_coords = []
        for di, dj in NEIGHBORS:
            ni, nj = i + di, j + dj
            if 0 <= ni < N and 0 <= nj < N:
                neighbor_vals.append(new_grid[ni, nj])
                neighbor_coords.append((ni, nj))
        
        if not neighbor_vals:
            continue
        
        #Среднее в окрестности
        avg = (new_grid[i, j] + sum(neighbor_vals)) / (1 + len(neighbor_vals))
        
        #Если текущая клетка выше среднего - отдаём 1 единицу наименьшему соседу
        if new_grid[i, j] > avg and new_grid[i, j] > 0:
            min_idx = int(np.argmin(neighbor_vals))
            ni, nj = neighbor_coords[min_idx]
            if new_grid[ni, nj] < NUM_STATES - 1:
                new_grid[i, j] -= 1
                new_grid[ni, nj] += 1
    
    return new_grid

#Функция состояния - однородная функция первого порядка (линейная)
#f(λ·x) = λ·f(x), т.е. просто сумма значений на произвольном подмножестве клеток
def conservation_quantity(grid):
    return int(grid.sum())

#Основной цикл моделирования
def run_simulation():
    print("=" * 60)
    print("Клеточный автомат с законом сохранения")
    print("=" * 60)
    
    grid = init_grid()
    S0 = conservation_quantity(grid)
    print(f"Размер поля: {GRID_SIZE}x{GRID_SIZE}")
    print(f"Множество состояний: {{0, 1, ..., {NUM_STATES-1}}}")
    print(f"Начальное значение сохраняемой величины S = {S0}")
    print(f"Закон сохранения: S = Σ grid[i,j] = const")
    print(f"Параметр однородности функции состояния: 1 (линейная)")
    print()
    
    saved_states = {0: grid.copy()}
    conservation_history = [S0]
    
    for t in range(1, MAX_STEPS + 1):
        grid = step(grid, t)
        S = conservation_quantity(grid)
        conservation_history.append(S)
        
        if t in DISPLAY_STEPS:
            saved_states[t] = grid.copy()
        
        if t % 50 == 0:
            print(f"  Ход {t:4d}: S = {S} (отклонение от S0: {S - S0})")
    
    #Проверка закона сохранения
    violations = [s for s in conservation_history if s != S0]
    if not violations:
        print(f"\nЗакон сохранения выполнен на всех {MAX_STEPS} шагах: S = {S0}")
    else:
        print(f"\nОШИБКА: закон сохранения нарушен на {len(violations)} шагах!")
    
    return saved_states, conservation_history

#Визуализация
def visualize(saved_states, conservation_history):
    steps_shown = sorted(saved_states.keys())[:5]
    
    fig = plt.figure(figsize=(15, 8))
    gs = fig.add_gridspec(2, 5, height_ratios=[1, 0.9], hspace=0.4, wspace=0.25)
    
    for i, t in enumerate(steps_shown):
        ax = fig.add_subplot(gs[0, i])
        im = ax.imshow(saved_states[t], cmap='YlOrRd', vmin=0, vmax=NUM_STATES-1,
                       interpolation='nearest')
        ax.set_title(f'Ход {t}\nS = {conservation_quantity(saved_states[t])}', fontsize=10)
        ax.set_xticks([0, 50, 99]); ax.set_yticks([0, 50, 99])
        ax.tick_params(labelsize=7)
    
    ax_s = fig.add_subplot(gs[1, :])
    ax_s.plot(conservation_history, color='darkgreen', linewidth=1.5)
    ax_s.set_xlabel('Ход', fontsize=11)
    ax_s.set_ylabel('S (сохраняемая величина)', fontsize=11)
    ax_s.set_title('Контроль закона сохранения S = Σ grid[i,j]', fontsize=11)
    ax_s.grid(True, alpha=0.3)
    S0 = conservation_history[0]
    ax_s.set_ylim(S0 - 10, S0 + 10)
    
    fig.suptitle("Клеточный автомат с законом сохранения (100×100)", fontsize=14, fontweight='bold')
    plt.savefig(OUT_DIR / 'result.png', dpi=120, bbox_inches='tight')
    plt.show()
    print("\nГрафик сохранён: result.png")

if __name__ == "__main__":
    saved, hist = run_simulation()
    visualize(saved, hist)
