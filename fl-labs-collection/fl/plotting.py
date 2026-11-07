from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PALETTE = ["#2b62a3", "#c8643b", "#23917a", "#b8860b", "#7d5ba6", "#b94a5e"]
INK = "#2b2b2b"
MUTED = "#6e6e6e"
GRID = "#e4e4e1"


def set_style():
    plt.rcParams.update({
        "figure.dpi": 110,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": "#b5b5b0",
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.titlepad": 24,
        "axes.labelsize": 10,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.frameon": False,
        "legend.fontsize": 9,
        "lines.linewidth": 1.8,
        "font.family": "DejaVu Sans",
        "axes.prop_cycle": plt.cycler(color=PALETTE),
    })


def save(fig, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)


def end_labels(ax, values, x, min_gap):
    order = sorted(range(len(values)), key=lambda i: values[i])
    placed = []
    for i in order:
        y = values[i] if not placed else max(values[i], placed[-1] + min_gap)
        placed.append(y)
        ax.annotate(f"{values[i]:.3f}", (x, values[i]), xytext=(x + 0.4, y), textcoords="data",
                    fontsize=8, color=MUTED, va="center")


def subtitle(ax, text: str):
    ax.text(0, 1.025, text, transform=ax.transAxes, fontsize=9, color=MUTED, va="bottom")
