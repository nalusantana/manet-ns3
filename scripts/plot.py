#!/usr/bin/env python3
"""
plot.py — gera as figuras a partir de data/processed/summary_*.csv.

Experimento base (velocidade):
    pdr_vs_speed, throughput_vs_speed, delay_vs_speed, jitter_vs_speed,
    comparativo_10ms, metricas_vs_velocidade

Variável adicional (taxa de transmissão, 10 m/s):
    pdr_vs_rate, throughput_vs_rate, delay_vs_rate, jitter_vs_rate,
    comparativo_rate, metricas_vs_rate

Cada figura é gravada em PDF e PNG (300 dpi), com a média das execuções e
barras de erro de IC 95% (t-Student).

Uso:
    python3 scripts/plot.py
    python3 scripts/plot.py --processed data/processed --figures figures
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd

# Cache gravável do matplotlib dentro do repositório.
_REPO = Path(__file__).resolve().parent.parent
os.environ.setdefault("MPLCONFIGDIR", str(_REPO / ".mplconfig"))
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

# Data fixa no metadado dos PDFs, para figuras reproduzíveis.
os.environ.setdefault("SOURCE_DATE_EPOCH", "1767225600")

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# ---------------------------------------------------------------------------
# Estilo
# ---------------------------------------------------------------------------
plt.rcParams.update(
    {
        "font.size": 10,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linestyle": ":",
        "axes.axisbelow": True,
        "figure.dpi": 110,
        "savefig.bbox": "tight",
    }
)

PROTOCOL_ORDER = ["AODV", "OLSR", "DSDV"]
STYLE = {
    "AODV": dict(color="#d62728", marker="o", linestyle="-", label="AODV (reativo)"),
    "OLSR": dict(color="#1f77b4", marker="s", linestyle="--", label="OLSR (proativo)"),
    "DSDV": dict(color="#2ca02c", marker="^", linestyle=":", label="DSDV (proativo)"),
}
SPEED_ORDER = [1, 5, 10, 20]
RATE_ORDER = ["256kbps", "512kbps", "1Mbps", "2Mbps"]
RATE_LABELS = {"256kbps": "256 kbps", "512kbps": "512 kbps", "1Mbps": "1 Mbps", "2Mbps": "2 Mbps"}

METRICS = [
    ("pdrPct", "PDR", "%", "pdr"),
    ("throughputMbps", "Throughput", "Mbps", "throughput"),
    ("delayMs", "Atraso médio", "ms", "delay"),
    ("jitterMs", "Jitter médio", "ms", "jitter"),
]


def load(summary_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(summary_csv)
    return df


def series(df: pd.DataFrame, metric: str, proto: str, var: str):
    sub = df[(df["metric"] == metric) & (df["protocol"] == proto)]
    sub = sub.set_index(var)
    order = SPEED_ORDER if var == "speed" else RATE_ORDER
    sub = sub.reindex([v for v in order if v in sub.index])
    return sub


def _uniform_n(df: pd.DataFrame, stem: str) -> int:
    """n por célula, exigindo que seja uniforme — o título das figuras usa esse n.

    Usar ``max()`` superestimaria o n se alguma célula tivesse perdido execuções
    (por NaN, por exemplo); aqui isso vira erro em vez de figura enganosa.
    """
    ns = sorted({int(v) for v in df["n"].unique()})
    if len(ns) != 1:
        raise SystemExit(
            f"ERRO: n não uniforme no resumo '{stem}': {ns}. "
            "Rode scripts/analyze.py sobre um lote completo."
        )
    return ns[0]


def save(fig, figures: Path, name: str) -> None:
    fig.savefig(figures / f"{name}.pdf")
    fig.savefig(figures / f"{name}.png", dpi=300)
    plt.close(fig)
    print(f"  -> {figures / name}.pdf / .png")


def line_figure(df, metric, title, ylabel, var, figures, fname):
    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    for proto in PROTOCOL_ORDER:
        s = series(df, metric, proto, var)
        if s.empty:
            continue
        x = list(s.index)
        st = STYLE[proto]
        ax.errorbar(
            x,
            s["mean"],
            yerr=s["ci95_half"],
            capsize=3.5,
            linewidth=1.6,
            markersize=6,
            markeredgecolor="black",
            markeredgewidth=0.4,
            **st,
        )
    if var == "speed":
        ax.set_xlabel("Velocidade dos nós (m/s)")
        ax.set_xticks(SPEED_ORDER)
    else:
        ax.set_xlabel("Taxa oferecida por fluxo")
        ax.set_xticks(range(len(RATE_ORDER)))
        ax.set_xticklabels([RATE_LABELS[r] for r in RATE_ORDER])
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    if metric in ("delayMs", "jitterMs"):
        # atraso e jitter nao podem ser negativos; o IC alto do DSDV a 1 m/s
        # produziria barras abaixo de zero
        ax.set_ylim(bottom=0)
    ax.legend(frameon=False, fontsize=8.5)
    save(fig, figures, fname)


def bar_figure(df, var, value, figures, fname, suptitle):
    """Barras agregadas comparando os protocolos em uma condição fixa.

    A unidade vai no título do painel; rótulos verticais em quatro painéis lado
    a lado se sobrepõem. ``constrained_layout`` cuida do espaçamento.
    """
    fig, axes = plt.subplots(1, 4, figsize=(5.2, 1.65), constrained_layout=True)
    width = 0.6
    x = range(len(PROTOCOL_ORDER))
    for ax, (metric, label, unit, _) in zip(axes, METRICS):
        means, errs, colors = [], [], []
        for proto in PROTOCOL_ORDER:
            s = series(df, metric, proto, var)
            if value in s.index:
                means.append(float(s.loc[value, "mean"]))
                errs.append(float(s.loc[value, "ci95_half"]))
            else:
                means.append(0.0)
                errs.append(0.0)
            colors.append(STYLE[proto]["color"])
        ax.bar(
            x,
            means,
            width,
            yerr=errs,
            capsize=2.5,
            color=colors,
            edgecolor="black",
            linewidth=0.5,
        )
        ax.set_xticks(list(x))
        ax.set_xticklabels(PROTOCOL_ORDER, fontsize=9.5)
        ax.set_title(f"{label}\n({unit})", fontsize=10)
        ax.tick_params(axis="y", labelsize=9.5)
        if metric in ("delayMs", "jitterMs"):
            ax.set_ylim(bottom=0)
    fig.suptitle(suptitle, fontsize=11)
    save(fig, figures, fname)


def panel_figure(df, var, figures, fname, suptitle):
    # figsize pequeno com fontes grandes: a figura é reduzida na página, então o
    # que importa é a fonte efetiva final.
    fig, axes = plt.subplots(2, 2, figsize=(5.8, 3.3))
    for ax, (metric, label, unit, _) in zip(axes.ravel(), METRICS):
        for proto in PROTOCOL_ORDER:
            s = series(df, metric, proto, var)
            if s.empty:
                continue
            st = STYLE[proto]
            ax.errorbar(
                list(s.index),
                s["mean"],
                yerr=s["ci95_half"],
                capsize=2.5,
                linewidth=1.3,
                markersize=4.5,
                markeredgecolor="black",
                markeredgewidth=0.3,
                **st,
            )
        ax.set_title(f"{label} ({unit})", fontsize=13)
        ax.tick_params(labelsize=12)
        if metric in ("delayMs", "jitterMs"):
            ax.set_ylim(bottom=0)
        if var == "speed":
            ax.set_xlabel("Velocidade (m/s)", fontsize=12)
            ax.set_xticks(SPEED_ORDER)
        else:
            ax.set_xlabel("Taxa por fluxo", fontsize=12)
            ax.set_xticks(range(len(RATE_ORDER)))
            ax.set_xticklabels([RATE_LABELS[r] for r in RATE_ORDER], fontsize=11)
    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, frameon=False, fontsize=11.5)
    fig.suptitle(suptitle, fontsize=13)
    fig.tight_layout(rect=(0, 0.05, 1, 0.96))
    save(fig, figures, fname)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--processed", default="data/processed")
    ap.add_argument("--figures", default="figures")
    args = ap.parse_args()

    processed, figures = Path(args.processed), Path(args.figures)
    figures.mkdir(parents=True, exist_ok=True)

    base_csv = processed / "summary_base.csv"
    rate_csv = processed / "summary_rate.csv"

    if not base_csv.exists() and not rate_csv.exists():
        print(
            f"Nada a fazer: nenhum resumo em '{processed}/'. "
            "Rode antes: python3 scripts/analyze.py"
        )
        return 0

    if base_csv.exists():
        base = load(base_csv)
        n_runs = _uniform_n(base, "base")
        print(f"Figuras do experimento base (variável: velocidade, n = {n_runs})")
        for metric, label, unit, short in METRICS:
            line_figure(
                base,
                metric,
                f"{label} × velocidade",
                f"{label} ({unit})",
                "speed",
                figures,
                f"{short}_vs_speed",
            )
        bar_figure(
            base,
            "speed",
            10,
            figures,
            "comparativo_10ms",
            f"Comparativo dos protocolos a 10 m/s (média ± IC 95%, n = {n_runs})",
        )
        panel_figure(base, "speed", figures, "metricas_vs_velocidade", "Efeito da mobilidade (1–20 m/s)")

    if rate_csv.exists():
        rate = load(rate_csv)
        n_runs = _uniform_n(rate, "rate")
        print(f"Figuras da variável adicional (taxa de transmissão, 10 m/s, n = {n_runs})")
        for metric, label, unit, short in METRICS:
            line_figure(
                rate,
                metric,
                f"{label} × taxa oferecida",
                f"{label} ({unit})",
                "rate",
                figures,
                f"{short}_vs_rate",
            )
        bar_figure(
            rate,
            "rate",
            "1Mbps",
            figures,
            "comparativo_rate",
            f"Comparativo dos protocolos a 1 Mbps por fluxo (média ± IC 95%, n = {n_runs})",
        )
        panel_figure(rate, "rate", figures, "metricas_vs_rate", "Efeito da carga oferecida (256 kbps–2 Mbps)")

    print("Figuras gravadas em", figures)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
