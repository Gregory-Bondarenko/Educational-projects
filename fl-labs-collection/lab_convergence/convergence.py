import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT.parent))
from fl.data import load_data, make_partition
from fl.federated import Config, local_update, rounds_to, run
from fl.model import accuracy, init_model, train_gd
from fl.plotting import MUTED, PALETTE, save, set_style, subtitle

FIG, RES = ROOT / "images", ROOT / "results"
ALPHA = 0.5
TARGETS = (0.8, 0.9, 0.93)


def identity_check(X, y, parts, lr=1.0):
    W0, b0 = init_model(X.shape[1])
    cfg = Config(local_epochs=1, lr=lr)
    sizes = np.array([len(p) for p in parts], dtype=float)
    weights = sizes / sizes.sum()
    local = [local_update(X[p], y[p], W0, b0, cfg) for p in parts]
    W_fed = sum(w * m[0] for w, m in zip(weights, local))
    b_fed = sum(w * m[1] for w, m in zip(weights, local))
    #при E = 1 раунд FedAvg должен совпасть с шагом GD на объединённых данных клиентов
    pooled = np.concatenate(parts)
    W_gd, b_gd = train_gd(X[pooled], y[pooled], W0, b0, 1, lr)
    return float(max(np.abs(W_fed - W_gd).max(), np.abs(b_fed - b_gd).max()))


def plot_iid_vs_noniid(curves, central, path):
    fig, ax = plt.subplots(figsize=(7.5, 4))
    for (label, acc), color in zip(curves.items(), PALETTE):
        ax.plot(range(1, len(acc) + 1), acc, color=color, label=label)
    ax.axhline(central, color=MUTED, lw=1, ls="--")
    ax.text(1, central + 0.005, f"централизованное обучение {central:.3f}", fontsize=8, color=MUTED)
    for t in TARGETS:
        ax.axhline(t, color="#d7d7d3", lw=0.8, ls=":")
    ax.set_ylim(0.6, 1.0)
    ax.set_xlabel("раунд")
    ax.set_ylabel("точность на тесте")
    ax.set_title("Неоднородность замедляет путь, но почти не сдвигает финиш")
    subtitle(ax, f"FedAvg, 10 клиентов, E = 5, Non-IID: Дирихле α = {ALPHA}")
    ax.legend(loc="lower right")
    save(fig, path)


def plot_epochs(curves, path):
    fig, ax = plt.subplots(figsize=(7.5, 4))
    for (epochs, acc), color in zip(curves.items(), PALETTE):
        ax.plot(range(1, len(acc) + 1), acc, color=color, label=f"E = {epochs}")
    ax.axhline(0.9, color="#d7d7d3", lw=0.8, ls=":")
    ax.set_ylim(0.6, 1.0)
    ax.set_xlabel("раунд")
    ax.set_ylabel("точность на тесте")
    ax.set_title("Больше локальной работы, меньше раундов")
    subtitle(ax, f"Non-IID α = {ALPHA}, 30 раундов")
    ax.legend(loc="lower right")
    save(fig, path)


def plot_compute_vs_comm(df, path):
    fig, ax = plt.subplots(figsize=(7, 3.8))
    sub = df.dropna(subset=["rounds_to_0.9"])
    ax.plot(sub["rounds_to_0.9"], sub["local_epochs_to_0.9"], marker="o", color=PALETTE[0])
    for _, r in sub.iterrows():
        ax.annotate(f"E = {int(r.local_epochs)}", (r["rounds_to_0.9"], r["local_epochs_to_0.9"]),
                    xytext=(6, 2), textcoords="offset points", fontsize=8, color=MUTED)
    ax.set_xlabel("раундов связи до точности 0.9")
    ax.set_ylabel("локальных эпох на клиенте до 0.9")
    ax.set_title("E покупает раунды вычислениями")
    subtitle(ax, f"Non-IID α = {ALPHA}; при α = 0.1 точность 0.9 за 30 раундов не достигнута ни при одном E")
    ax.grid(axis="both")
    save(fig, path)


def main():
    set_style()
    RES.mkdir(exist_ok=True)
    X_tr, y_tr, X_te, y_te = load_data()
    iid = make_partition(y_tr, "iid")
    non = make_partition(y_tr, "noniid", alpha=ALPHA)
    hard = make_partition(y_tr, "noniid", alpha=0.1)

    def fit(parts, **kw):
        return run(X_tr, y_tr, X_te, y_te, parts, Config(**kw))["accuracy"]

    W0, b0 = init_model(X_tr.shape[1])
    central_hist = []
    W, b = W0, b0
    for _ in range(300):
        W, b = train_gd(X_tr, y_tr, W, b, 1, 1.0)
        central_hist.append(accuracy(X_te, y_te, W, b))
    central = central_hist[-1]

    def describe(acc):
        return {**{f"rounds_to_{t}": rounds_to(acc, t) for t in TARGETS}, "final": acc[-1], "best": acc.max()}

    base = {"IID": fit(iid, rounds=60), f"Non-IID α = {ALPHA}": fit(non, rounds=60),
            "Non-IID α = 0.1": fit(hard, rounds=60)}
    table1 = pd.DataFrame({k: describe(v) for k, v in base.items()}).T
    plot_iid_vs_noniid(base, central, FIG / "iid_vs_noniid_60_rounds.png")

    e1 = pd.DataFrame({k: describe(fit(p, local_epochs=1, rounds=30)) for k, p in
                       [("IID", iid), (f"Non-IID α = {ALPHA}", non), ("Non-IID α = 0.1", hard)]}).T

    sweep_rows, curves = [], {}
    for name, parts in [(f"α = {ALPHA}", non), ("α = 0.1", hard)]:
        for epochs in (1, 5, 20):
            acc = fit(parts, local_epochs=epochs)
            if name == f"α = {ALPHA}":
                curves[epochs] = acc
            r = describe(acc)
            r09 = r["rounds_to_0.9"]
            sweep_rows.append({"scenario": name, "local_epochs": epochs, **r,
                               "local_epochs_to_0.9": r09 * epochs if r09 else None})
    sweep = pd.DataFrame(sweep_rows)
    plot_epochs(curves, FIG / "local_epochs_sweep.png")
    plot_compute_vs_comm(sweep, FIG / "compute_vs_communication.png")

    prox_rows = []
    for name, parts in [(f"α = {ALPHA}", non), ("α = 0.1", hard)]:
        for mu, lr in [(0.0, 1.0), (0.1, 1.0), (1.0, 1.0), (1.0, 0.5)]:
            acc = fit(parts, local_epochs=20, mu=mu, lr=lr)
            prox_rows.append({"scenario": name, "mu": mu, "lr": lr, **describe(acc)})
    prox = pd.DataFrame(prox_rows)

    gap = identity_check(X_tr, y_tr, non)

    table1.to_csv(RES / "iid_vs_noniid.csv")
    e1.to_csv(RES / "e1.csv")
    sweep.to_csv(RES / "epochs_sweep.csv", index=False)
    prox.to_csv(RES / "fedprox.csv", index=False)
    pd.Series({"central_300_epochs": central, "identity_max_abs_diff": gap}).to_csv(RES / "reference.csv", header=["value"])

    with pd.option_context("display.float_format", "{:.4f}".format, "display.width", 180):
        print(table1, e1, sweep, prox, f"central = {central:.4f}", f"E=1 identity max|diff| = {gap:.2e}", sep="\n\n")


if __name__ == "__main__":
    main()
