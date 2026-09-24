from pathlib import Path
#Импорт библиотек
import numpy as np
import matplotlib.pyplot as plt

OUT_DIR = Path(__file__).resolve().parent

#Параметры клеточного автомата
GRID_SIZE = 100
MAX_STEPS = 300
DISPLAY_STEPS = [0, 10, 50, 150, 300]

#Вероятность самопроизвольного прорастания растения (семена, занесённые ветром).
#Без неё растительность, съеденная в каком-то районе, уже никогда туда не возвращается
REGROWTH_PROB = 0.003

#Множество состояний каждого слоя: {0, 1}
#Слой 1 - «растительность» (ресурс): растёт, если рядом есть другие растения
#Слой 2 - «травоядные» (потребитель): размножаются при наличии ресурса, гибнут без него
#(на клетке или рядом должно быть хотя бы 2 растения)
#Взаимодействие между слоями: травоядные поедают растительность

#Окрестность Мура (8 соседей)
#Граничные условия: отсутствующие клетки - в состоянии "0"

#Инициализация: случайное размещение с фиксированным seed
def init_grids():
    rng = np.random.default_rng(seed=42)
    #Слой 1: растительность (30% заполнение)
    layer1 = (rng.random((GRID_SIZE, GRID_SIZE)) < 0.30).astype(np.int8)
    #Слой 2: травоядные (5% заполнение, размещаются случайно по полю)
    layer2 = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.int8)
    candidates = rng.random((GRID_SIZE, GRID_SIZE)) < 0.05
    layer2[candidates] = 1
    return layer1, layer2

#Подсчёт соседей в окрестности Мура (граничные условия - нули за пределами поля)
def count_neighbors(grid):
    N = GRID_SIZE
    padded = np.pad(grid, 1, mode='constant', constant_values=0)
    n = np.zeros((N, N), dtype=int)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue
            n += padded[1+di:N+1+di, 1+dj:N+1+dj]
    return n

#Один шаг эволюции двухслойного автомата
def step(layer1, layer2, rng):
    n1 = count_neighbors(layer1)   # соседи-растения
    n2 = count_neighbors(layer2)   # соседи-травоядные

    new_l1 = np.zeros_like(layer1)
    new_l2 = np.zeros_like(layer2)

    #Правила для слоя 1 (растительность):
    #Живая клетка выживает, если 2-5 соседей-растений И нет травоядного на этой клетке
    #Мёртвая клетка оживает, если ровно 3 соседа-растения И нет травоядного,
    #либо прорастает сама с вероятностью REGROWTH_PROB
    alive1 = layer1 == 1
    herbivore_here = layer2 == 1
    survive1 = alive1 & (n1 >= 2) & (n1 <= 5) & ~herbivore_here
    sprout = rng.random(layer1.shape) < REGROWTH_PROB
    born1 = ~alive1 & ((n1 == 3) | sprout) & ~herbivore_here
    new_l1 = (survive1 | born1).astype(np.int8)

    #Правила для слоя 2 (травоядные):
    #Живое травоядное выживает, если есть еда (растение на клетке или хотя бы 2 рядом)
    #и 1-4 соседа-травоядных; без еды или при перенаселении погибает
    #Мёртвая клетка рождает травоядное, если 2-3 соседа-травоядных И на клетке есть растение
    #Травоядное поедает растение при контакте (учтено в слое 1 выше)
    alive2 = layer2 == 1
    food_here = layer1 == 1
    has_food = food_here | (n1 >= 2)
    survive2 = alive2 & has_food & (n2 >= 1) & (n2 <= 4)
    born2 = ~alive2 & food_here & (n2 >= 2) & (n2 <= 3)
    new_l2 = (survive2 | born2).astype(np.int8)

    return new_l1, new_l2

#Основной цикл моделирования
def run_simulation():
    print("=" * 60)
    print("Двухслойный клеточный автомат (растительность - травоядные)")
    print("=" * 60)

    layer1, layer2 = init_grids()
    rng = np.random.default_rng(seed=7)
    print(f"Размер поля: {GRID_SIZE}x{GRID_SIZE}")
    print(f"Множество состояний каждого слоя: {{0, 1}}")
    print(f"Слой 1 (растительность): {int(layer1.sum())} живых клеток")
    print(f"Слой 2 (травоядные): {int(layer2.sum())} живых клеток")
    print(f"Окрестность: Мура (8 соседей)")
    print(f"Граничные условия: нулевые (отсутствующие клетки = 0)")
    print()

    saved = {0: (layer1.copy(), layer2.copy())}
    pop1 = [int(layer1.sum())]
    pop2 = [int(layer2.sum())]

    for t in range(1, MAX_STEPS + 1):
        layer1, layer2 = step(layer1, layer2, rng)
        pop1.append(int(layer1.sum()))
        pop2.append(int(layer2.sum()))

        if t in DISPLAY_STEPS:
            saved[t] = (layer1.copy(), layer2.copy())

        if t % 50 == 0:
            print(f"  Ход {t:4d}: растений = {pop1[-1]:5d}, травоядных = {pop2[-1]:5d}")

    return saved, pop1, pop2

#Визуализация
def visualize(saved, pop1, pop2):
    steps_shown = sorted(saved.keys())[:5]

    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(3, 5, height_ratios=[1, 1, 0.9], hspace=0.4, wspace=0.25)

    #Верхний ряд - слой 1 (растительность)
    for i, t in enumerate(steps_shown):
        ax = fig.add_subplot(gs[0, i])
        ax.imshow(saved[t][0], cmap='Greens', vmin=0, vmax=1, interpolation='nearest')
        ax.set_title(f'Ход {t}\nраст: {int(saved[t][0].sum())}', fontsize=9)
        ax.set_xticks([]); ax.set_yticks([])
    fig.text(0.02, 0.82, 'Слой 1\n(растения)', fontsize=10, fontweight='bold',
             va='center', rotation=90)

    #Средний ряд - слой 2 (травоядные)
    for i, t in enumerate(steps_shown):
        ax = fig.add_subplot(gs[1, i])
        ax.imshow(saved[t][1], cmap='Oranges', vmin=0, vmax=1, interpolation='nearest')
        ax.set_title(f'трав: {int(saved[t][1].sum())}', fontsize=9)
        ax.set_xticks([]); ax.set_yticks([])
    fig.text(0.02, 0.53, 'Слой 2\n(травоядн.)', fontsize=10, fontweight='bold',
             va='center', rotation=90)

    #Нижний ряд - динамика популяций
    ax_pop = fig.add_subplot(gs[2, :])
    ax_pop.plot(pop1, color='green', linewidth=1.5, label='Растительность (слой 1)')
    ax_pop.plot(pop2, color='darkorange', linewidth=1.5, label='Травоядные (слой 2)')
    ax_pop.set_xlabel('Ход', fontsize=11)
    ax_pop.set_ylabel('Число живых клеток', fontsize=11)
    ax_pop.set_title('Динамика популяций двухслойного клеточного автомата', fontsize=11)
    ax_pop.legend(fontsize=10)
    ax_pop.grid(True, alpha=0.3)

    fig.suptitle("Двухслойный клеточный автомат (100×100)", fontsize=14, fontweight='bold')
    plt.savefig(OUT_DIR / 'result.png', dpi=120, bbox_inches='tight')
    plt.show()
    print("\nГрафик сохранён: result.png")

if __name__ == "__main__":
    saved, p1, p2 = run_simulation()
    visualize(saved, p1, p2)
