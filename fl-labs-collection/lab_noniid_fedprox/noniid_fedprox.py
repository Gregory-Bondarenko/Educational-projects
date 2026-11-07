import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT.parent))
from fl.data import class_counts, load_data, make_partition
from fl.federated import Config, run
from fl.plotting import MUTED, PALETTE, save, set_style, subtitle

FIG, RES = ROOT / "images", ROOT / "results"
DROP_SEEDS = range(5)
MUS = (0.0, 0.01, 0.1, 0.5, 1.0)


def favourites(counts: np.ndarray, share: float = 0.8) -> pd.DataFrame:
    rows = []
    for k, row in enumerate(counts):
        order = np.argsort(row)[::-1]
        cum = np.cumsum(row[order]) / row.sum()
        n_fav = int(np.searchsorted(cum, share) + 1)
        rows.append({
            "client": k, "n": int(row.sum()),
            "favourites": ", ".join(str(c) for c in order[:n_fav]),
            "n_favourites": n_fav, "favourites_share": cum[n_fav - 1],
            "classes_lt_5": int((row < 5).sum()),
        })
    return pd.DataFrame(rows)


def plot_heatmap(counts, path):
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    im = ax.imshow(counts, cmap="Blues", aspect="auto")
    for i in range(counts.shape[0]):
        for j in range(counts.shape[1]):
            value = counts[i, j]
            ax.text(j, i, value, ha="center", va="center", fontsize=7.5,
                    color="white" if value > counts.max() * 0.55 else "#3a3a3a")
    ax.set_xticks(range(10))
    ax.set_yticks(range(counts.shape[0]))
    ax.set_xlabel("класс (цифра)")
    ax.set_ylabel("клиент")
    ax.grid(False)
    ax.set_title("Разбиение Дирихле, α = 0.1: у каждого клиента свои цифры")
    fig.colorbar(im, ax=ax, shrink=0.8, label="число примеров")
    save(fig, path)


def plot_curves(curves, path):
    fig, ax = plt.subplots(figsize=(7, 3.8))
    for (label, acc), color in zip(curves.items(), PALETTE):
        ax.plot(range(1, len(acc) + 1), acc, color=color, label=label)
        ax.annotate(f"{acc[-1]:.3f}", (len(acc), acc[-1]), xytext=(4, 0), textcoords="offset points",
                    fontsize=8, color=MUTED, va="center")
    ax.set_xlabel("раунд")
    ax.set_ylabel("точность на тесте")
    ax.set_ylim(0.3, 1.0)
    ax.set_title("FedAvg на неоднородных данных выходит на полку")
    subtitle(ax, "10 клиентов, 5 локальных эпох")
    ax.legend(loc="lower right")
    save(fig, path)


def plot_dropout(drop_curves, path):
    fig, ax = plt.subplots(figsize=(7, 3.8))
    for (drop, curves), color in zip(drop_curves.items(), PALETTE):
        arr = np.vstack(curves)
        rounds = np.arange(1, arr.shape[1] + 1)
        ax.fill_between(rounds, arr.min(axis=0), arr.max(axis=0), color=color, alpha=0.15, lw=0)
        ax.plot(rounds, arr.mean(axis=0), color=color, label=f"drop = {drop}")
    ax.set_xlabel("раунд")
    ax.set_ylabel("точность на тесте")
    ax.set_title("Выпадение клиентов раскачивает обучение")
    subtitle(ax, f"Non-IID α = 0.1; линия: среднее, полоса: min–max по {len(DROP_SEEDS)} запускам")
    ax.legend(loc="lower right")
    save(fig, path)


def plot_mu(df, path):
    fig, ax = plt.subplots(figsize=(7, 3.8))
    for (label, sub), color in zip(df.groupby("setup", sort=False), PALETTE):
        xs = np.arange(len(sub))
        ax.plot(xs, sub.final_acc, marker="o", color=color, label=label)
        offset = -0.07 if label.startswith("α = 0.1") else 0.04
        for x, v in zip(xs, sub.final_acc):
            ax.text(x, v + offset, f"{v:.3f}", ha="center", fontsize=8, color=color)
    ax.set_xticks(np.arange(len(MUS)), [str(m) for m in MUS])
    ax.set_xlabel("μ (0 соответствует FedAvg)")
    ax.set_ylabel("финальная точность")
    ax.set_ylim(-0.05, 1.05)
    ax.set_title("FedProx на выпуклой задаче: чем сильнее резинка, тем хуже")
    subtitle(ax, "20 локальных эпох, 30 раундов, lr = 1.0")
    ax.legend(loc="lower left")
    save(fig, path)


def plot_retention(total, kept, recall_course, recall_fixed, path):
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.8))
    x = np.arange(10)
    axes[0].bar(x, total, color="#d9d9d5", width=0.7, label="в обучающей выборке")
    axes[0].bar(x, kept, color=PALETTE[0], width=0.7, label="попало к клиентам")
    axes[0].set_xticks(x)
    axes[0].set_xlabel("класс")
    axes[0].set_ylabel("число примеров")
    axes[0].set_title("Разбиение из методички теряет данные")
    axes[0].legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2)
    axes[1].bar(x - 0.19, recall_course, width=0.36, color=PALETTE[1], label="разбиение методички")
    axes[1].bar(x + 0.19, recall_fixed, width=0.36, color=PALETTE[0], label="исправленное разбиение")
    axes[1].set_xticks(x)
    axes[1].set_ylim(0, 1.05)
    axes[1].set_xlabel("класс")
    axes[1].set_ylabel("recall на тесте")
    axes[1].set_title("Потерянные классы FedAvg почти не узнаёт")
    axes[1].legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2)
    save(fig, path)


def main():
    set_style()
    RES.mkdir(exist_ok=True)
    X_tr, y_tr, X_te, y_te = load_data()
    iid = make_partition(y_tr, "iid")
    noniid = make_partition(y_tr, "noniid", alpha=0.1)

    def fit(parts, **kw):
        return run(X_tr, y_tr, X_te, y_te, parts, Config(**kw))["accuracy"]

    counts = class_counts(y_tr, noniid)
    fav = favourites(counts)
    plot_heatmap(counts, FIG / "dirichlet_class_heatmap.png")

    acc_iid, acc_non = fit(iid), fit(noniid)
    checkpoints = pd.DataFrame({
        "round": [1, 10, 20, 30],
        "iid": acc_iid[[0, 9, 19, 29]],
        "noniid_a01": acc_non[[0, 9, 19, 29]],
    })
    plot_curves({"IID": acc_iid, "Non-IID, α = 0.1": acc_non}, FIG / "iid_vs_noniid.png")

    drop_curves, drop_rows = {}, []
    for drop in (0.0, 0.3, 0.5):
        curves = [fit(noniid, drop=drop, drop_seed=s) for s in DROP_SEEDS]
        drop_curves[drop] = curves
        finals = [c[-1] for c in curves]
        drop_rows.append({"drop": drop, "final_mean": np.mean(finals), "final_min": np.min(finals),
                          "final_max": np.max(finals), "best_mean": np.mean([c.max() for c in curves]),
                          "finals": " / ".join(f"{v:.4f}" for v in finals)})
    drop_df = pd.DataFrame(drop_rows)
    plot_dropout(drop_curves, FIG / "dropout_stability.png")
    drop_iid = [fit(iid, drop=0.5, drop_seed=s)[-1] for s in DROP_SEEDS]

    mu_rows = []
    for mu in MUS:
        acc = fit(noniid, local_epochs=20, mu=mu)
        mu_rows.append({"setup": "α = 0.1, 10 клиентов", "mu": mu, "final_acc": acc[-1], "best_acc": acc.max()})
    hard = make_partition(y_tr, "noniid", n_clients=30, alpha=0.05)
    for mu in MUS:
        acc = fit(hard, local_epochs=20, mu=mu)
        mu_rows.append({"setup": "α = 0.05, 30 клиентов", "mu": mu, "final_acc": acc[-1], "best_acc": acc.max()})
    mu_df = pd.DataFrame(mu_rows)
    plot_mu(mu_df, FIG / "fedprox_mu_sweep.png")

    check = pd.DataFrame({
        "lr": [1.0, 0.5, 0.5],
        "mu": [1.0, 1.0, 0.0],
        "final_acc": [fit(noniid, local_epochs=20, mu=1.0)[-1],
                      fit(noniid, local_epochs=20, mu=1.0, lr=0.5)[-1],
                      fit(noniid, local_epochs=20, lr=0.5)[-1]],
    })
    same = np.allclose(fit(noniid, mu=0.0), acc_non)

    #контроль: то же разбиение, но без потери доли последнего клиента
    fixed = make_partition(y_tr, "noniid", alpha=0.1, keep_all=True)
    res_course = run(X_tr, y_tr, X_te, y_te, noniid, Config())
    res_fixed = run(X_tr, y_tr, X_te, y_te, fixed, Config())

    def recall(model):
        pred = (X_te @ model[0] + model[1]).argmax(axis=1)
        return np.array([(pred[y_te == c] == c).mean() for c in range(10)])

    kept = np.bincount(y_tr[np.unique(np.concatenate(noniid))], minlength=10)
    total = np.bincount(y_tr, minlength=10)
    plot_retention(total, kept, recall(res_course["model"]), recall(res_fixed["model"]), FIG / "partition_data_loss.png")
    hard_fixed = make_partition(y_tr, "noniid", n_clients=30, alpha=0.05, keep_all=True)
    hard_check = pd.DataFrame({
        "partition": ["методичка", "исправленное"],
        "examples_used": [len(np.unique(np.concatenate(hard))), len(np.unique(np.concatenate(hard_fixed)))],
        "fedavg_e20_final_acc": [fit(hard, local_epochs=20)[-1], fit(hard_fixed, local_epochs=20)[-1]],
    })
    hard_check.to_csv(RES / "partition_check_hard.csv", index=False)
    partition_check = pd.DataFrame({
        "partition": ["методичка", "исправленное"],
        "examples_used": [len(np.unique(np.concatenate(noniid))), len(np.unique(np.concatenate(fixed)))],
        "fedavg_final_acc": [res_course["accuracy"][-1], res_fixed["accuracy"][-1]],
        "fedavg_e20_final_acc": [fit(noniid, local_epochs=20)[-1], fit(fixed, local_epochs=20)[-1]],
    })
    retention = pd.DataFrame({"class": range(10), "total": total, "kept": kept,
                              "recall_course": recall(res_course["model"]), "recall_fixed": recall(res_fixed["model"])})
    partition_check.to_csv(RES / "partition_check.csv", index=False)
    retention.to_csv(RES / "class_retention.csv", index=False)

    fav.to_csv(RES / "class_favourites.csv", index=False)
    pd.DataFrame(counts).to_csv(RES / "class_counts.csv")
    checkpoints.to_csv(RES / "checkpoints.csv", index=False)
    drop_df.to_csv(RES / "dropout.csv", index=False)
    mu_df.to_csv(RES / "fedprox_mu.csv", index=False)
    check.to_csv(RES / "fedprox_lr_check.csv", index=False)

    with pd.option_context("display.float_format", "{:.4f}".format, "display.width", 160, "display.max_colwidth", 60):
        print(fav, checkpoints, drop_df, f"IID drop 0.5: {np.round(drop_iid, 4)}", mu_df, check,
              f"mu=0 воспроизводит FedAvg: {same}", partition_check, retention, sep="\n\n")


if __name__ == "__main__":
    main()
