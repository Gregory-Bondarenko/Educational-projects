import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.datasets import load_digits

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT.parent))
from fl.model import accuracy, gradients, per_example_loss, softmax, train_gd
from fl.plotting import MUTED, PALETTE, save, set_style, subtitle

FIG, RES = ROOT / "images", ROOT / "results"
SEED, N_CLIENTS, ALPHA, LR = 42, 10, 0.5, 0.5


def split_noniid(alpha=ALPHA, holdout=False):
    rng = np.random.default_rng(SEED)
    data = load_digits()
    X, y = data.data / 16.0, data.target
    pool = np.arange(len(y))
    test_idx = None
    if holdout:
        test_idx = rng.permutation(pool)[:600]
        pool = np.setdiff1d(pool, test_idx)
    parts = {c: [] for c in range(N_CLIENTS)}
    for cls in np.unique(y):
        idx = pool[y[pool] == cls]
        rng.shuffle(idx)
        cuts = (np.cumsum(rng.dirichlet(np.full(N_CLIENTS, alpha))) * len(idx)).astype(int)[:-1]
        for c, chunk in enumerate(np.split(idx, cuts)):
            parts[c].extend(chunk)
    #так тест формируется в скрипте курса: из всех данных, уже розданных клиентам
    if test_idx is None:
        test_idx = rng.permutation(np.arange(len(y)))[:600]
    clients = [np.array(parts[c]) for c in range(N_CLIENTS)]
    return X, y, clients, test_idx


def mia(W, b, X_in, y_in, X_out, y_out):
    loss_in = per_example_loss(X_in, y_in, W, b)
    loss_out = per_example_loss(X_out, y_out, W, b)
    #порог посередине между средними loss: учебная сбалансированная атака
    threshold = (loss_in.mean() + loss_out.mean()) / 2
    attack_acc = ((loss_in < threshold).mean() + (loss_out >= threshold).mean()) / 2
    return float(attack_acc), loss_in, loss_out


def train_dp(X, y, W, b, epochs, clip, sigma, rng):
    n = len(X)
    for _ in range(epochs):
        P = softmax(X @ W + b)
        P[np.arange(n), y] -= 1.0
        G = np.einsum("ni,nk->nik", X, P)
        norms = np.sqrt((G ** 2).sum(axis=(1, 2)) + (P ** 2).sum(axis=1))
        #обрезка градиента каждого примера до нормы clip, как в DP-SGD
        k = np.minimum(1.0, clip / norms)
        noise_W = rng.normal(0, sigma * clip / n, G.shape[1:])
        noise_b = rng.normal(0, sigma * clip / n, P.shape[1:])
        W = W - LR * (np.einsum("n,nik->ik", k, G) / n + noise_W)
        b = b - LR * ((k[:, None] * P).sum(axis=0) / n + noise_b)
    return W, b


def run_mia(X, y, clients, test_idx, epochs, client=0, clip=None, sigma=0.0):
    rng = np.random.default_rng(SEED)
    own = clients[client]
    W, b = np.zeros((64, 10)), np.zeros(10)
    if clip is None:
        W, b = train_gd(X[own], y[own], W, b, epochs, LR)
    else:
        W, b = train_dp(X[own], y[own], W, b, epochs, clip, sigma, rng)
    #не-члены берутся только из тех же классов, иначе атака мерит перекос классов
    outsiders = test_idx[np.isin(y[test_idx], np.unique(y[own]))]
    attack_acc, loss_in, loss_out = mia(W, b, X[own], y[own], X[outsiders], y[outsiders])
    return {
        "attack_acc": attack_acc,
        "own_acc": accuracy(X[own], y[own], W, b),
        "loss_members": loss_in.mean(),
        "loss_non_members": loss_out.mean(),
        "overlap": int(np.isin(outsiders, own).sum()),
        "losses": (loss_in, loss_out),
    }


def run_fl(X, y, clients, test_idx, rounds=30, epochs=5, frac_mal=0.0, attack="flip", agg="mean"):
    W, b = np.zeros((64, 10)), np.zeros(10)
    n_mal = int(round(frac_mal * N_CLIENTS))
    weights = np.array([len(c) for c in clients], dtype=float)
    weights /= weights.sum()
    history = []
    for _ in range(rounds):
        updates = []
        for cid, idx in enumerate(clients):
            Wl, bl = train_gd(X[idx], y[idx], W.copy(), b.copy(), epochs, LR)
            dW, db = Wl - W, bl - b
            if cid < n_mal:
                factor = -3.0 if attack == "flip" else 20.0
                dW, db = factor * dW, factor * db
            updates.append((dW, db))
        if agg == "median":
            dW = np.median(np.stack([u[0] for u in updates]), axis=0)
            db = np.median(np.stack([u[1] for u in updates]), axis=0)
        else:
            dW = sum(w * u[0] for w, u in zip(weights, updates))
            db = sum(w * u[1] for w, u in zip(weights, updates))
        W, b = W + dW, b + db
        history.append(accuracy(X[test_idx], y[test_idx], W, b))
    return np.array(history)


def plot_losses(losses, path):
    loss_in, loss_out = losses
    fig, ax = plt.subplots(figsize=(7, 3.8))
    bins = np.linspace(0, max(loss_in.max(), loss_out.max()), 40)
    ax.hist(loss_out, bins=bins, color=PALETTE[1], alpha=0.55, label="не-члены (посторонние)")
    ax.hist(loss_in, bins=bins, color=PALETTE[0], alpha=0.75, label="члены (данные клиента)")
    threshold = (loss_in.mean() + loss_out.mean()) / 2
    ax.axvline(threshold, color=MUTED, lw=1.2, ls="--")
    ax.text(threshold, ax.get_ylim()[1] * 0.92, "  порог атаки", color=MUTED, fontsize=9)
    ax.set_xlabel("cross-entropy loss примера")
    ax.set_ylabel("число примеров")
    ax.set_title("Модель клиента узнаёт свои данные по величине loss")
    subtitle(ax, "клиент 0, 20 локальных эпох, без защит")
    ax.legend()
    save(fig, path)


def plot_dp(clip_df, noise_df, path):
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
    for ax, df, x, xlabel, title in [
        (axes[0], clip_df, "clip", "порог обрезки C", "Обрезка градиентов"),
        (axes[1], noise_df, "sigma", "шум σ (при C = 1.0)", "Обрезка и шум"),
    ]:
        xs = np.arange(len(df))
        ax.plot(xs, df["own_acc"], marker="o", color=PALETTE[2], label="точность на своих данных")
        ax.plot(xs, df["attack_acc"], marker="o", color=PALETTE[5], label="точность атаки")
        ax.axhline(0.5, color=MUTED, lw=1, ls=":")
        ax.set_xticks(xs, df[x].astype(str))
        ax.set_xlabel(xlabel)
        ax.set_title(title)
    axes[0].text(0, 0.51, "случайное угадывание", color=MUTED, fontsize=8)
    axes[0].set_ylim(0.4, 1.0)
    axes[0].legend(loc="upper right")
    save(fig, path)


def plot_attacks(df, path):
    fig, ax = plt.subplots(figsize=(7, 3.8))
    for (agg, attack), color, style in [(("mean", "flip"), PALETTE[1], "-"), (("median", "flip"), PALETTE[0], "-"),
                                        (("mean", "inflate"), PALETTE[1], "--"), (("median", "inflate"), PALETTE[0], "--")]:
        sub = df[(df["agg"] == agg) & (df["attack"] == attack)]
        ax.plot(sub.frac_mal, sub.final_acc, marker="o", ls=style, color=color, label=f"{agg}, {attack}")
    ax.set_xlabel("доля вредителей")
    ax.set_ylabel("точность на тесте после 30 раундов")
    ax.set_ylim(0, 1)
    ax.set_title("Медиана выдерживает вредителей, среднее нет")
    subtitle(ax, "сплошная линия: flip (−3·Δ), пунктир: inflate (20·Δ)")
    ax.legend(loc="lower left")
    save(fig, path)


def main():
    set_style()
    RES.mkdir(exist_ok=True)
    X, y, clients, test_idx = split_noniid()
    print("размеры клиентов:", [len(c) for c in clients])

    base = run_fl(X, y, clients, test_idx)
    print(f"baseline: раунд 1 = {base[0]:.4f}, раунд 30 = {base[-1]:.4f}")

    mia_rows = []
    for epochs in (5, 20):
        r = run_mia(X, y, clients, test_idx, epochs)
        mia_rows.append({"epochs": epochs, **{k: v for k, v in r.items() if k != "losses"}})
        if epochs == 20:
            plot_losses(r["losses"], FIG / "mia_loss_distribution.png")
    mia_df = pd.DataFrame(mia_rows)

    per_client = pd.DataFrame([{
        "client": k, "n": len(clients[k]),
        **{key: v for key, v in run_mia(X, y, clients, test_idx, 20, client=k).items() if key != "losses"},
    } for k in range(N_CLIENTS)])

    clip_df = pd.DataFrame([{"clip": c, **{k: v for k, v in run_mia(X, y, clients, test_idx, 20, clip=c).items() if k != "losses"}}
                            for c in (3.0, 1.0, 0.3)])
    noise_df = pd.DataFrame([{"sigma": s, **{k: v for k, v in run_mia(X, y, clients, test_idx, 20, clip=1.0, sigma=s).items() if k != "losses"}}
                             for s in (0.0, 1.0, 3.0)])
    plot_dp(clip_df, noise_df, FIG / "dp_clip_noise.png")

    attack_rows = []
    for attack in ("flip", "inflate"):
        for agg in ("mean", "median"):
            for f in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5):
                hist = run_fl(X, y, clients, test_idx, frac_mal=f, attack=attack, agg=agg)
                attack_rows.append({"attack": attack, "agg": agg, "frac_mal": f,
                                    "final_acc": hist[-1], "best_acc": hist.max()})
    attack_df = pd.DataFrame(attack_rows)
    plot_attacks(attack_df, FIG / "byzantine_mean_vs_median.png")

    X, y, clients_h, test_h = split_noniid(holdout=True)
    clean = {
        "baseline_final_acc": run_fl(X, y, clients_h, test_h)[-1],
        "mia_e20": run_mia(X, y, clients_h, test_h, 20)["attack_acc"],
        "flip_mean_0.2": run_fl(X, y, clients_h, test_h, frac_mal=0.2)[-1],
        "flip_median_0.2": run_fl(X, y, clients_h, test_h, frac_mal=0.2, agg="median")[-1],
    }

    pd.DataFrame({"round": np.arange(1, 31), "accuracy": base}).to_csv(RES / "baseline.csv", index=False)
    mia_df.to_csv(RES / "mia.csv", index=False)
    per_client.to_csv(RES / "mia_per_client.csv", index=False)
    clip_df.to_csv(RES / "dp_clip.csv", index=False)
    noise_df.to_csv(RES / "dp_noise.csv", index=False)
    attack_df.to_csv(RES / "byzantine.csv", index=False)
    pd.Series(clean).to_csv(RES / "holdout_control.csv", header=["value"])

    with pd.option_context("display.float_format", "{:.4f}".format, "display.width", 160):
        print(mia_df, per_client, clip_df, noise_df, attack_df.pivot_table(index=["attack", "agg"], columns="frac_mal", values="final_acc"),
              pd.Series(clean), sep="\n\n")


if __name__ == "__main__":
    main()
