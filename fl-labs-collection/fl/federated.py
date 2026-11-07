from dataclasses import dataclass

import numpy as np

from .model import accuracy, gradients, init_model


@dataclass
class Config:
    rounds: int = 30
    local_epochs: int = 5
    lr: float = 1.0
    mu: float = 0.0
    server: str = "avg"
    server_lr: float = 1.0
    beta: float = 0.9
    beta1: float = 0.9
    beta2: float = 0.99
    tau: float = 1e-3
    scaffold: bool = False
    drop: float = 0.0
    quant_bits: int = 32
    topk: float = 1.0
    ef: bool = False
    n_malicious: int = 0
    attack: str = "flip"
    agg: str = "mean"
    seed: int = 42
    drop_seed: int | None = None


class Server:
    def __init__(self, W, b, cfg: Config):
        self.W, self.b, self.cfg = W, b, cfg
        self.m = [np.zeros_like(W), np.zeros_like(b)]
        self.v = [np.zeros_like(W), np.zeros_like(b)]
        self.t = 0

    def step(self, delta: list[np.ndarray]):
        cfg = self.cfg
        params = [self.W, self.b]
        #delta уже направлена к моделям клиентов, поэтому шаг сервера со знаком плюс
        if cfg.server == "avg":
            params = [p + d for p, d in zip(params, delta)]
        elif cfg.server == "avgm":
            self.m = [cfg.beta * m + d for m, d in zip(self.m, delta)]
            params = [p + cfg.server_lr * m for p, m in zip(params, self.m)]
        elif cfg.server == "adam":
            self.t += 1
            self.m = [cfg.beta1 * m + (1 - cfg.beta1) * d for m, d in zip(self.m, delta)]
            self.v = [cfg.beta2 * v + (1 - cfg.beta2) * d * d for v, d in zip(self.v, delta)]
            m_hat = [m / (1 - cfg.beta1 ** self.t) for m in self.m]
            v_hat = [v / (1 - cfg.beta2 ** self.t) for v in self.v]
            params = [p + cfg.server_lr * m / (np.sqrt(v) + cfg.tau)
                      for p, m, v in zip(params, m_hat, v_hat)]
        else:
            raise ValueError(cfg.server)
        self.W, self.b = params


def local_update(X, y, W_glob, b_glob, cfg: Config, control=None):
    W, b = W_glob.copy(), b_glob.copy()
    for _ in range(cfg.local_epochs):
        gW, gb = gradients(X, y, W, b)
        #проксимальный член FedProx тянет клиента обратно к глобальной модели
        if cfg.mu > 0:
            gW = gW + cfg.mu * (W - W_glob)
            gb = gb + cfg.mu * (b - b_glob)
        #SCAFFOLD: убираем личный дрейф клиента и добавляем общее направление
        if control is not None:
            (ckW, ckb), (cW, cb) = control
            gW = gW - ckW + cW
            gb = gb - ckb + cb
        W, b = W - cfg.lr * gW, b - cfg.lr * gb
    return W, b


def quantize(delta: np.ndarray, bits: int, rng: np.random.RandomState) -> np.ndarray:
    scale = max(np.abs(delta).max(), 1e-12)
    #при одном бите сетка вырождается в ноль, поэтому передаём только знак
    if bits == 1:
        up = rng.rand(*delta.shape) < (1 + delta / scale) / 2
        return np.where(up, scale, -scale)
    levels = 2 ** (bits - 1) - 1
    u = delta / scale * levels
    q = np.floor(u)
    #стохастическое округление: вверх с вероятностью дробной части, E[Q(x)] = x
    q += (rng.rand(*delta.shape) < u - q).astype(delta.dtype)
    return q / levels * scale


def sparsify(delta: np.ndarray, frac: float, residual: np.ndarray, value_bits: int, ef: bool):
    eff = delta + residual
    k = max(1, int(round(frac * eff.size)))
    idx = np.argpartition(np.abs(eff).ravel(), -k)[-k:]
    sparse = np.zeros_like(eff)
    sparse.ravel()[idx] = eff.ravel()[idx]
    #error feedback: выброшенный остаток доедет в следующем раунде
    new_residual = eff - sparse if ef else np.zeros_like(eff)
    #каждая координата стоит значения и 32-битного индекса
    return sparse, new_residual, k * (value_bits + 32) / 8


def run(X_train, y_train, X_test, y_test, parts, cfg: Config) -> dict:
    n_clients = len(parts)
    W, b = init_model(X_train.shape[1], cfg.seed)
    server = Server(W, b, cfg)
    n_params = W.size + b.size
    value_bits = min(cfg.quant_bits, 32)

    controls = [[np.zeros_like(W), np.zeros_like(b)] for _ in range(n_clients)]
    c_global = [np.zeros_like(W), np.zeros_like(b)]
    residuals = [[np.zeros_like(W), np.zeros_like(b)] for _ in range(n_clients)]
    rng_drop = np.random.RandomState(cfg.seed + 1 if cfg.drop_seed is None else cfg.drop_seed)
    rng_quant = np.random.RandomState(cfg.seed + 2)

    acc_hist, bytes_hist = [], []
    for _ in range(cfg.rounds):
        active = [k for k in range(n_clients) if rng_drop.rand() >= cfg.drop]
        if not active:
            active = [int(rng_drop.randint(n_clients))]

        W_glob, b_glob = server.W.copy(), server.b.copy()
        deltas, sizes, new_controls, round_bytes = [], [], [], 0.0
        for k in active:
            Xk, yk = X_train[parts[k]], y_train[parts[k]]
            control = (controls[k], c_global) if cfg.scaffold else None
            Wk, bk = local_update(Xk, yk, W_glob, b_glob, cfg, control)
            delta = [Wk - W_glob, bk - b_glob]

            if cfg.scaffold:
                scale = cfg.local_epochs * cfg.lr
                controls[k] = [ck - c + d / -scale for ck, c, d in zip(controls[k], c_global, delta)]
                new_controls.append(controls[k])

            #вредители: flip разворачивает обновление, inflate раздувает его
            if k < cfg.n_malicious:
                factor = -3.0 if cfg.attack == "flip" else 20.0
                delta = [factor * d for d in delta]

            if cfg.quant_bits < 32:
                delta = [quantize(d, cfg.quant_bits, rng_quant) for d in delta]
            if cfg.topk < 1.0:
                packed = [sparsify(d, cfg.topk, r, value_bits, cfg.ef) for d, r in zip(delta, residuals[k])]
                delta = [p[0] for p in packed]
                residuals[k] = [p[1] for p in packed]
                round_bytes += sum(p[2] for p in packed)
            else:
                round_bytes += n_params * value_bits / 8

            deltas.append(delta)
            sizes.append(len(parts[k]))

        weights = np.array(sizes, dtype=float) / sum(sizes)
        if cfg.agg == "median":
            step = [np.median(np.stack([d[i] for d in deltas]), axis=0) for i in range(2)]
        else:
            step = [sum(w * d[i] for w, d in zip(weights, deltas)) for i in range(2)]
        server.step(step)

        #общий контроль SCAFFOLD усредняется с теми же весами, что и модели
        if cfg.scaffold:
            c_global = [sum(w * c[i] for w, c in zip(weights, new_controls)) for i in range(2)]

        acc_hist.append(accuracy(X_test, y_test, server.W, server.b))
        bytes_hist.append(round_bytes / len(active))

    return {
        "accuracy": np.array(acc_hist),
        "bytes_per_round": float(np.mean(bytes_hist)),
        "baseline_bytes": 4 * n_params,
        "model": (server.W, server.b),
    }


def rounds_to(acc: np.ndarray, target: float):
    hit = np.flatnonzero(acc >= target)
    return int(hit[0] + 1) if hit.size else None
