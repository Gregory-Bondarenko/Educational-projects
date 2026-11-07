import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT.parent))
from fl.data import load_data, make_partition
from fl.federated import Config, run
from fl.plotting import MUTED, PALETTE, save, set_style, subtitle

FIG, RES = ROOT / "images", ROOT / "results"
BITS = (32, 8, 6, 4, 3, 2, 1)
OFFSETS = {"4 бита + top-k 10% + EF": (-40, -16), "3 бита": (2, 6), "4 бита": (-12, 7), "2 бита": (6, 3),
           "top-k 10% + EF": (6, 2), "top-k 10%": (6, -8), "FedAvg": (6, 3)}


def pareto(df):
    front, best = [], -1.0
    for _, r in df.sort_values(["savings", "final_acc"], ascending=False).iterrows():
        if r.final_acc > best:
            front.append(r)
            best = r.final_acc
    return pd.DataFrame(front).sort_values("savings")


def plot_bits(df, path):
    fig, ax = plt.subplots(figsize=(7, 3.8))
    xs = np.arange(len(df))
    ax.plot(xs, df.final_acc, marker="o", color=PALETTE[0])
    for x, (acc, sv) in enumerate(zip(df.final_acc, df.savings)):
        ax.annotate(f"{acc:.3f}\n×{sv:.0f}", (x, acc), xytext=(0, -26), textcoords="offset points",
                    ha="center", fontsize=8, color=MUTED)
    ax.set_xticks(xs, [f"{b} бит" if b >= 5 or b == 1 else f"{b} бита" for b in df.bits])
    ax.set_ylim(0.80, 0.86)
    ax.set_ylabel("финальная точность")
    ax.set_title("До 4 бит квантизация бесплатна")
    subtitle(ax, "стохастическое округление, Non-IID α = 0.1, 30 раундов; под точкой экономия трафика")
    save(fig, path)


def plot_tradeoff(df, path):
    fig, ax = plt.subplots(figsize=(8, 4.6))
    groups = {"оптимизаторы": PALETTE[2], "квантизация": PALETTE[0], "разрежение": PALETTE[1], "базис": MUTED}
    for group, color in groups.items():
        sub = df[df.group == group]
        ax.scatter(sub.savings, sub.final_acc, s=46, color=color, label=group, zorder=3,
                   edgecolors="white", linewidths=1.2)
        for _, r in sub.iterrows():
            dx, dy = OFFSETS.get(r.config, (6, 3))
            ax.annotate(r.config, (r.savings, r.final_acc), xytext=(dx, dy), textcoords="offset points",
                        fontsize=7.5, color=MUTED)
    front = pareto(df)
    ax.step(front.savings, front.final_acc, where="post", color="#9a9a96", lw=1, ls="--", zorder=2)
    ax.set_xscale("log", base=2)
    ax.set_xticks([0.5, 1, 2, 4, 8, 16, 32], ["×0.5", "×1", "×2", "×4", "×8", "×16", "×32"])
    ax.set_xlabel("экономия трафика относительно float32 FedAvg")
    ax.set_ylabel("финальная точность")
    ax.grid(axis="both")
    ax.set_title("Кривая размена: биты против качества")
    subtitle(ax, "пунктир: парето-фронтир")
    ax.legend(loc="center right")
    save(fig, path)


def main():
    set_style()
    RES.mkdir(exist_ok=True)
    X_tr, y_tr, X_te, y_te = load_data()
    parts = make_partition(y_tr, "noniid", alpha=0.1)

    def fit(p=parts, **kw):
        r = run(X_tr, y_tr, X_te, y_te, p, Config(**kw))
        return {"final_acc": r["accuracy"][-1], "best_acc": r["accuracy"].max(),
                "bytes": r["bytes_per_round"], "savings": r["baseline_bytes"] / r["bytes_per_round"]}

    bits_df = pd.DataFrame([{"bits": b, **fit(quant_bits=b)} for b in BITS])
    plot_bits(bits_df[bits_df.bits > 1], FIG / "quantization_bits.png")

    sparse_rows = [
        ("float32 (база)", {}), ("top-k 10% без EF", {"topk": 0.1}), ("top-k 10% с EF", {"topk": 0.1, "ef": True}),
        ("4 бита + top-k 10% + EF", {"quant_bits": 4, "topk": 0.1, "ef": True}),
        ("top-k 5% с EF", {"topk": 0.05, "ef": True}), ("top-k 1% с EF", {"topk": 0.01, "ef": True}),
        ("4 бита + top-k 1% + EF", {"quant_bits": 4, "topk": 0.01, "ef": True}),
    ]
    sparse_df = pd.DataFrame([{"scheme": name, **fit(**kw)} for name, kw in sparse_rows])

    trade = [
        ("FedAvg", "базис", {}),
        ("FedAvgM", "оптимизаторы", {"server": "avgm"}), ("FedAdam", "оптимизаторы", {"server": "adam", "server_lr": 0.5}),
        *[(label, "квантизация", {"quant_bits": b}) for label, b in [("8 бит", 8), ("4 бита", 4), ("3 бита", 3), ("2 бита", 2)]],
        ("top-k 10%", "разрежение", {"topk": 0.1}), ("top-k 10% + EF", "разрежение", {"topk": 0.1, "ef": True}),
        ("4 бита + top-k 10% + EF", "разрежение", {"quant_bits": 4, "topk": 0.1, "ef": True}),
        ("FedAvgM + 4 бита", "оптимизаторы", {"server": "avgm", "quant_bits": 4}),
    ]
    trade_df = pd.DataFrame([{"config": n, "group": g, **fit(**kw)} for n, g, kw in trade])
    scaffold = fit(scaffold=True)
    #SCAFFOLD передаёт модель и контроль, трафик вдвое больше
    scaffold["savings"] /= 2
    trade_df.loc[len(trade_df)] = {"config": "SCAFFOLD", "group": "оптимизаторы", **scaffold}
    plot_tradeoff(trade_df, FIG / "tradeoff_pareto.png")

    hard = make_partition(y_tr, "noniid", n_clients=30, alpha=0.05)
    hard_df = pd.DataFrame([{"scheme": n, **fit(hard, **kw)} for n, kw in [
        ("float32", {}), ("4 бита", {"quant_bits": 4}), ("2 бита", {"quant_bits": 2}),
        ("4 бита + top-k 10% + EF", {"quant_bits": 4, "topk": 0.1, "ef": True})]])

    for name, df in [("quantization", bits_df), ("sparsification", sparse_df), ("tradeoff", trade_df), ("hard_mode", hard_df)]:
        df.to_csv(RES / f"{name}.csv", index=False)
    with pd.option_context("display.float_format", "{:.4f}".format, "display.width", 180):
        print(bits_df, sparse_df, trade_df, pareto(trade_df)[["config", "savings", "final_acc"]], hard_df, sep="\n\n")


if __name__ == "__main__":
    main()
