import sys
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT.parent))
from fl.plotting import MUTED, PALETTE, save, set_style, subtitle

FIG, RES = ROOT / "images", ROOT / "results"
RNG = np.random.default_rng(42)


@dataclass
class Client:
    name: str
    X: np.ndarray
    y: np.ndarray


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))


def accuracy(X, y, w, b):
    return float(((sigmoid(X @ w + b) >= 0.5) == y).mean())


def log_loss(X, y, w, b):
    p = sigmoid(X @ w + b)
    return float(-(y * np.log(p + 1e-9) + (1 - y) * np.log(1 - p + 1e-9)).mean())


def gd_step(X, y, w, b, lr):
    err = sigmoid(X @ w + b) - y
    return w - lr * X.T @ err / len(X), b - lr * err.mean()


def make_client(name, n, shift_x1, shift_x2, threshold):
    x1 = RNG.normal(shift_x1, 1.0, n)
    x2 = RNG.normal(shift_x2, 1.2, n)
    score = 1.2 * x1 - 0.8 * x2 + RNG.normal(0, 0.6, n)
    return Client(name, np.column_stack([x1, x2]), (score > threshold).astype(int))


def train_central(X, y, epochs=200, lr=0.1):
    w, b, hist = np.zeros(X.shape[1]), 0.0, []
    for _ in range(epochs):
        w, b = gd_step(X, y, w, b, lr)
        hist.append(log_loss(X, y, w, b))
    return w, b, hist


def train_fedavg(clients, rounds=30, local_epochs=5, lr=0.1):
    X_all = np.vstack([c.X for c in clients])
    y_all = np.concatenate([c.y for c in clients])
    total = len(X_all)
    w, b, hist = np.zeros(2), 0.0, []
    for _ in range(rounds):
        agg_w, agg_b = np.zeros(2), 0.0
        for c in clients:
            wl, bl = w.copy(), b
            for _ in range(local_epochs):
                wl, bl = gd_step(c.X, c.y, wl, bl, lr)
            agg_w += len(c.X) / total * wl
            agg_b += len(c.X) / total * bl
        w, b = agg_w, agg_b
        hist.append(log_loss(X_all, y_all, w, b))
    return w, b, hist


def comm_cost(n_clients, model_dim, rounds):
    return n_clients * model_dim * 2 * rounds


def plot_clients(clients):
    fig, ax = plt.subplots(figsize=(7, 4.6))
    for c, color in zip(clients, PALETTE):
        ax.scatter(*c.X[c.y == 1].T, s=14, color=color, alpha=0.75, label=f"{c.name}, класс 1")
        ax.scatter(*c.X[c.y == 0].T, s=14, facecolors="none", edgecolors=color, alpha=0.6, linewidths=0.8)
    ax.set_xlabel("x1")
    ax.set_ylabel("x2")
    ax.grid(axis="both")
    ax.set_title("Клиенты живут в разных областях признакового пространства")
    subtitle(ax, "заливка: класс 1, контур: класс 0")
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
    save(fig, FIG / "clients_feature_space.png")


def plot_losses(hist_c, runs):
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
    axes[0].plot(range(1, len(hist_c) + 1), hist_c, color=PALETTE[0])
    axes[0].set_title("Централизованное обучение")
    axes[0].set_xlabel("эпоха")
    axes[0].set_ylabel("log loss на объединённой выборке")
    for (label, hist), color in zip(runs.items(), PALETTE[1:]):
        axes[1].plot(range(1, len(hist) + 1), hist, color=color, label=label)
    axes[1].set_title("FedAvg")
    axes[1].set_xlabel("раунд")
    axes[1].legend()
    save(fig, FIG / "loss_curves.png")


def plot_per_client(df):
    fig, ax = plt.subplots(figsize=(7, 3.8))
    x = np.arange(len(df))
    ax.bar(x - 0.19, df["central_acc"], width=0.36, color=PALETTE[0], label="централизованная")
    ax.bar(x + 0.19, df["federated_acc"], width=0.36, color=PALETTE[1], label="FedAvg")
    for i, row in df.reset_index(drop=True).iterrows():
        ax.text(i - 0.19, row.central_acc + 0.01, f"{row.central_acc:.3f}", ha="center", fontsize=8, color=MUTED)
        ax.text(i + 0.19, row.federated_acc + 0.01, f"{row.federated_acc:.3f}", ha="center", fontsize=8, color=MUTED)
    ax.set_xticks(x, df["client"])
    ax.set_ylim(0.5, 1.02)
    ax.set_ylabel("accuracy")
    ax.set_title("Качество по клиентам")
    ax.legend(loc="lower right")
    save(fig, FIG / "per_client_accuracy.png")


def main():
    set_style()
    clients = [
        make_client("client_A", 220, -1.0, 0.4, -0.1),
        make_client("client_B", 260, 0.7, -0.6, 0.4),
        make_client("client_C", 180, 1.4, 0.9, 0.9),
    ]
    X_all = np.vstack([c.X for c in clients])
    y_all = np.concatenate([c.y for c in clients])

    stats = pd.DataFrame([{
        "client": c.name, "n": len(c.X), "share_class_1": c.y.mean(),
        "mean_x1": c.X[:, 0].mean(), "mean_x2": c.X[:, 1].mean(),
    } for c in clients])

    w_c, b_c, hist_c = train_central(X_all, y_all)
    setups = {"30 раундов, E = 5": (30, 5), "50 раундов, E = 3": (50, 3), "20 раундов, E = 8": (20, 8)}
    runs, rows, fed_models = {}, [], {}
    for label, (rounds, epochs) in setups.items():
        w_f, b_f, hist = train_fedavg(clients, rounds, epochs)
        runs[label], fed_models[label] = hist, (w_f, b_f)
        rows.append({
            "setup": label, "rounds": rounds, "local_epochs": epochs,
            "local_steps_total": rounds * epochs,
            "loss": log_loss(X_all, y_all, w_f, b_f), "acc": accuracy(X_all, y_all, w_f, b_f),
            "comm_scalars": comm_cost(len(clients), 3, rounds),
        })
    rows.insert(0, {"setup": "централизованная", "rounds": None, "local_epochs": None,
                    "local_steps_total": 200, "loss": log_loss(X_all, y_all, w_c, b_c),
                    "acc": accuracy(X_all, y_all, w_c, b_c), "comm_scalars": 0})
    summary = pd.DataFrame(rows)

    w_f, b_f = fed_models["30 раундов, E = 5"]
    per_client = pd.DataFrame([{
        "client": c.name,
        "central_acc": accuracy(c.X, c.y, w_c, b_c),
        "federated_acc": accuracy(c.X, c.y, w_f, b_f),
    } for c in clients])

    RES.mkdir(exist_ok=True)
    stats.to_csv(RES / "client_stats.csv", index=False)
    summary.to_csv(RES / "summary.csv", index=False)
    per_client.to_csv(RES / "per_client.csv", index=False)

    plot_clients(clients)
    plot_losses(hist_c, runs)
    plot_per_client(per_client)

    with pd.option_context("display.float_format", "{:.4f}".format, "display.width", 140):
        print(stats, summary, per_client, sep="\n\n")


if __name__ == "__main__":
    main()
