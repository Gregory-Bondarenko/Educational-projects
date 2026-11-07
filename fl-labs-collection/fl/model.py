import numpy as np

from .data import N_CLASSES


def softmax(z: np.ndarray) -> np.ndarray:
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def init_model(n_features: int, seed: int = 42):
    W = np.random.RandomState(seed).normal(scale=0.01, size=(n_features, N_CLASSES))
    return W, np.zeros(N_CLASSES)


def gradients(X: np.ndarray, y: np.ndarray, W: np.ndarray, b: np.ndarray):
    P = softmax(X @ W + b)
    P[np.arange(len(y)), y] -= 1.0
    return X.T @ P / len(X), P.sum(axis=0) / len(X)


def accuracy(X: np.ndarray, y: np.ndarray, W: np.ndarray, b: np.ndarray) -> float:
    return float(((X @ W + b).argmax(axis=1) == y).mean())


def per_example_loss(X: np.ndarray, y: np.ndarray, W: np.ndarray, b: np.ndarray) -> np.ndarray:
    P = softmax(X @ W + b)
    return -np.log(P[np.arange(len(y)), y] + 1e-9)


def train_gd(X: np.ndarray, y: np.ndarray, W: np.ndarray, b: np.ndarray, epochs: int, lr: float):
    for _ in range(epochs):
        gW, gb = gradients(X, y, W, b)
        W, b = W - lr * gW, b - lr * gb
    return W, b
