import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT.parent))
from fl.data import load_data, make_partition
from fl.federated import Config, run
from fl.plotting import MUTED, PALETTE, end_labels, save, set_style, subtitle

FIG, RES = ROOT / "images", ROOT / "results"


def plot_curves(curves, path, title, note):
    fig, ax = plt.subplots(figsize=(7.5, 4))
    for (label, acc), color in zip(curves.items(), PALETTE):
        ax.plot(range(1, len(acc) + 1), acc, color=color, label=label)
    end_labels(ax, [acc[-1] for acc in curves.values()], len(next(iter(curves.values()))), 0.018)
    ax.set_ylim(0.4, 1.0)
    ax.set_xlabel("раунд")
    ax.set_ylabel("точность на тесте")
    ax.set_title(title)
    subtitle(ax, note)
    ax.legend(loc="lower right")
    save(fig, path)


def plot_zoo(df, path):
    df = df.sort_values("final_acc")
    fig, ax = plt.subplots(figsize=(8, 4.2))
    colors = [PALETTE[1] if t > 1 else PALETTE[0] for t in df.traffic]
    ax.barh(df.algorithm, df.final_acc, color=colors, height=0.6)
    for i, (acc, t) in enumerate(zip(df.final_acc, df.traffic)):
        ax.text(acc + 0.004, i, f"{acc:.3f}   трафик {t:g}×", va="center", fontsize=8, color=MUTED)
    ax.set_xlim(0.75, 1.03)
    ax.grid(axis="x")
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("финальная точность после 30 раундов")
    ax.set_title("Зоопарк алгоритмов на Non-IID, α = 0.1")
    subtitle(ax, "синий: трафик как у FedAvg, терракотовый: SCAFFOLD передаёт модель и контроль")
    save(fig, path)


def plot_sweeps(beta_df, lr_df, path):
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), sharey=True)
    for ax, df, x, xlabel, title, color in [
        (axes[0], beta_df, "beta", "β", "FedAvgM: моментум", PALETTE[0]),
        (axes[1], lr_df, "server_lr", "η_s", "FedAdam: шаг сервера", PALETTE[2]),
    ]:
        xs = np.arange(len(df))
        ax.plot(xs, df.final_acc, marker="o", color=color, label="финальная")
        ax.plot(xs, df.best_acc, marker="o", color=color, alpha=0.4, ls="--", label="лучшая за прогон")
        ax.set_xticks(xs, df[x].astype(str))
        ax.set_xlabel(xlabel)
        ax.set_title(title)
    axes[0].set_ylabel("точность")
    axes[0].legend(loc="lower right")
    save(fig, path)


def main():
    set_style()
    RES.mkdir(exist_ok=True)
    X_tr, y_tr, X_te, y_te = load_data()
    parts = make_partition(y_tr, "noniid", alpha=0.1)
    iid = make_partition(y_tr, "iid")

    def fit(p=parts, **kw):
        return run(X_tr, y_tr, X_te, y_te, p, Config(**kw))["accuracy"]

    def row(name, acc, **extra):
        return {"config": name, **extra, "final_acc": acc[-1], "best_acc": acc.max()}

    curves = {
        "FedAvg": fit(),
        "FedAvgM, β = 0.9": fit(server="avgm"),
        "FedAdam, η_s = 0.1": fit(server="adam", server_lr=0.1),
        "FedAdam, η_s = 0.5": fit(server="adam", server_lr=0.5),
    }
    table1 = pd.DataFrame([row(k, v) for k, v in curves.items()])
    checks = pd.DataFrame([
        row("FedAvgM, β = 0 (вырожденный)", fit(server="avgm", beta=0.0)),
        row("FedAvgM со знаком минус", fit(server="avgm", server_lr=-1.0)),
        row("FedAvg IID", fit(iid)),
    ])
    plot_curves(curves, FIG / "server_optimizers.png", "Серверный оптимизатор возвращает потерю Non-IID",
                "Non-IID α = 0.1, E = 5, трафик как у FedAvg")

    table2 = pd.DataFrame([row("FedAvg + drop 0.3", fit(drop=0.3)),
                           row("FedAvgM + drop 0.3", fit(server="avgm", drop=0.3))])

    scaffold_curves = {
        "FedAvg, E = 5": fit(), "SCAFFOLD, E = 5": fit(scaffold=True),
        "FedAvg, E = 20": fit(local_epochs=20), "SCAFFOLD, E = 20": fit(scaffold=True, local_epochs=20),
    }
    table3 = pd.DataFrame([row(k, v) for k, v in scaffold_curves.items()])
    plot_curves(scaffold_curves, FIG / "scaffold.png", "SCAFFOLD вычитает систематический дрейф",
                "Non-IID α = 0.1, 30 раундов")

    zoo = pd.DataFrame([
        {"algorithm": "FedAvg (E = 5)", "idea": "базис", "traffic": 1, "bought": "точка отсчёта", "final_acc": curves["FedAvg"][-1]},
        {"algorithm": "FedAvg (E = 20)", "idea": "больше локальной работы", "traffic": 1, "bought": "раунды",
         "final_acc": scaffold_curves["FedAvg, E = 20"][-1]},
        {"algorithm": "FedProx (E = 20, μ = 0.1)", "idea": "штраф-резинка", "traffic": 1, "bought": "ничего",
         "final_acc": fit(local_epochs=20, mu=0.1)[-1]},
        {"algorithm": "FedAvgM (β = 0.9)", "idea": "моментум сервера", "traffic": 1, "bought": "стабильность",
         "final_acc": curves["FedAvgM, β = 0.9"][-1]},
        {"algorithm": "FedAdam (η_s = 0.5)", "idea": "адаптивный сервер", "traffic": 1, "bought": "сглаживание",
         "final_acc": curves["FedAdam, η_s = 0.5"][-1]},
        {"algorithm": "SCAFFOLD (E = 5)", "idea": "вычитание дрейфа", "traffic": 2, "bought": "прямая коррекция дрейфа",
         "final_acc": scaffold_curves["SCAFFOLD, E = 5"][-1]},
        {"algorithm": "SCAFFOLD (E = 20)", "idea": "вычитание дрейфа", "traffic": 2, "bought": "прямая коррекция дрейфа",
         "final_acc": scaffold_curves["SCAFFOLD, E = 20"][-1]},
    ])
    plot_zoo(zoo, FIG / "algorithm_zoo.png")

    beta_df = pd.DataFrame([row(f"β = {b}", fit(server="avgm", beta=b), beta=b) for b in (0.0, 0.5, 0.9, 0.95, 0.99)])
    lr_df = pd.DataFrame([row(f"η_s = {s}", fit(server="adam", server_lr=s), server_lr=s) for s in (0.05, 0.1, 0.3, 0.5, 1.0)])
    plot_sweeps(beta_df, lr_df, FIG / "hyperparameter_sweeps.png")

    hard = make_partition(y_tr, "noniid", n_clients=30, alpha=0.05)
    hard_df = pd.DataFrame([
        row("FedAvg", fit(hard)), row("FedAvgM", fit(hard, server="avgm")),
        row("FedAdam η_s = 0.5", fit(hard, server="adam", server_lr=0.5)),
        row("FedProx E = 20, μ = 0.1", fit(hard, local_epochs=20, mu=0.1)),
        row("SCAFFOLD E = 5", fit(hard, scaffold=True)), row("SCAFFOLD E = 20", fit(hard, scaffold=True, local_epochs=20)),
    ])

    fixed = make_partition(y_tr, "noniid", alpha=0.1, keep_all=True)
    fixed_df = pd.DataFrame([
        row("FedAvg", fit(fixed)), row("FedAvgM", fit(fixed, server="avgm")),
        row("FedAdam η_s = 0.5", fit(fixed, server="adam", server_lr=0.5)), row("SCAFFOLD E = 5", fit(fixed, scaffold=True)),
    ])

    for name, df in [("table1", table1), ("checks", checks), ("table2_drop", table2), ("table3_scaffold", table3),
                     ("zoo", zoo), ("beta_sweep", beta_df), ("adam_lr_sweep", lr_df),
                     ("hard_mode", hard_df), ("fixed_partition", fixed_df)]:
        df.to_csv(RES / f"{name}.csv", index=False)

    with pd.option_context("display.float_format", "{:.4f}".format, "display.width", 180):
        print(table1, checks, table2, table3, zoo, beta_df, lr_df, hard_df, fixed_df, sep="\n\n")


if __name__ == "__main__":
    main()
