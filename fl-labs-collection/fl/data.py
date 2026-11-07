import numpy as np
from sklearn.datasets import load_digits

N_CLASSES = 10


def load_data(test_size: float = 0.25, seed: int = 42):
    digits = load_digits()
    X = digits.data / 16.0
    y = digits.target.astype(int)
    #тест откладывается до разбиения по клиентам, иначе он пересечётся с их данными
    idx = np.random.RandomState(seed).permutation(len(X))
    n_test = int(len(X) * test_size)
    test_idx, train_idx = idx[:n_test], idx[n_test:]
    return X[train_idx], y[train_idx], X[test_idx], y[test_idx]


def partition_iid(y: np.ndarray, n_clients: int, seed: int = 42) -> list[np.ndarray]:
    idx = np.random.RandomState(seed).permutation(len(y))
    return np.array_split(idx, n_clients)


def partition_dirichlet(y: np.ndarray, n_clients: int, alpha: float, seed: int = 42,
                        min_size: int = 10, keep_all: bool = False) -> list[np.ndarray]:
    """keep_all=False повторяет разбиение из методички курса: остаток от floor
    перезаписывает долю последнего клиента, и часть примеров теряется."""
    rng = np.random.RandomState(seed)
    by_class = [np.where(y == c)[0] for c in range(N_CLASSES)]
    for idx in by_class:
        rng.shuffle(idx)

    client_idx = [[] for _ in range(n_clients)]
    for c in range(N_CLASSES):
        #доли класса c между клиентами: при малом alpha почти всё уходит одному-двум
        p = rng.dirichlet(np.full(n_clients, alpha))
        order = rng.permutation(len(by_class[c]))
        counts = np.floor(p * len(order)).astype(int)
        #в методичке здесь вычитается сумма вместе с долей последнего клиента, и она теряется
        counts[-1] = len(order) - (counts[:-1].sum() if keep_all else counts.sum())
        pos = 0
        for k in range(n_clients):
            client_idx[k].extend(by_class[c][order[pos:pos + counts[k]]])
            pos += counts[k]

    parts = []
    for k in range(n_clients):
        arr = np.array(client_idx[k], dtype=int)
        if len(arr) < min_size:
            arr = np.concatenate([arr, by_class[k % N_CLASSES][:min_size - len(arr)]])
        parts.append(arr)
    return parts


def make_partition(y: np.ndarray, mode: str, n_clients: int = 10, alpha: float = 0.1,
                   seed: int = 42, keep_all: bool = False) -> list[np.ndarray]:
    if mode == "iid":
        return partition_iid(y, n_clients, seed)
    return partition_dirichlet(y, n_clients, alpha, seed, keep_all=keep_all)


def class_counts(y: np.ndarray, parts: list[np.ndarray]) -> np.ndarray:
    return np.stack([np.bincount(y[idx], minlength=N_CLASSES) for idx in parts])
