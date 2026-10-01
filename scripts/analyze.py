#!/usr/bin/env python3
"""
analyze.py — validação, agregação e análise estatística do experimento MANET.

Entrada:
    data/raw/results_base.csv   (3 protocolos x 4 velocidades x R runs)
    data/raw/results_rate.csv   (3 protocolos x 4 taxas x R runs, 10 m/s)

O número de repetições R é lido dos próprios CSVs, de modo que o script serve
para qualquer R (5, 30, ...) sem alteração.

Saída (data/processed/):
    per_run_base.csv        métricas agregadas por execução
    per_run_rate.csv        métricas agregadas por execução
    summary_base.csv        média/min/máx/desvio-padrão/IC 95% por (protocolo, velocidade)
    summary_rate.csv        idem por (protocolo, taxa)
    tests_base.csv          Kruskal-Wallis por velocidade e métrica
    tests_rate.csv          Kruskal-Wallis por taxa e métrica
    posthoc_base.csv        Mann-Whitney par a par (correção de Holm)
    posthoc_rate.csv        idem
    efeito_base.csv         Kruskal-Wallis do fator dentro de cada protocolo
    efeito_rate.csv         idem
    relatorio_analise.md    relatório de validação e resultados

Unidade de análise: a execução. As métricas são agregadas dentro da execução
(somando/ponderando os 4 fluxos) e só depois resumidas entre as R execuções.

Uso:
    python3 scripts/analyze.py
    python3 scripts/analyze.py --raw data/raw --processed data/processed
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# ---------------------------------------------------------------------------
# Metadados do experimento
# ---------------------------------------------------------------------------
SPEED_ORDER = [1, 5, 10, 20]
RATE_ORDER = ["256kbps", "512kbps", "1Mbps", "2Mbps"]

# métricas resumidas: (coluna, rótulo, unidade, menor-é-melhor?)
METRICS = [
    ("pdrPct", "PDR", "%", False),
    ("deliveryRatioPct", "Razão de entrega", "%", False),
    ("throughputMbps", "Throughput", "Mbps", False),
    ("delayMs", "Atraso médio", "ms", True),
    ("jitterMs", "Jitter médio", "ms", True),
]

# tolerância para comparações numéricas
EPS = 1e-6


# ---------------------------------------------------------------------------
# Carregamento e validação
# ---------------------------------------------------------------------------
def load_raw(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo bruto não encontrado: {path}")
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    return df


def aggregate_per_run(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega os fluxos de cada execução em uma linha por execução.

    - Throughput: soma dos fluxos (vazão total da rede) [Mbps]
    - PDR / razão de entrega: razões de somas (não média de razões)
    - Atraso: média ponderada pela quantidade de pacotes recebidos
    - Jitter: média ponderada por (rxPackets - 1), como na definição do ns-3
    """
    keys = ["protocol", "speed", "run", "nodes", "seed", "rate"]
    # Nº de fluxos configurado; execuções em que o FlowMonitor não registrou um
    # fluxo têm o total oferecido reconstruído a partir desse número.
    flows_configured = int(df.groupby(keys).size().max())
    rows = []
    for key, g in df.groupby(keys, sort=False):
        protocol, speed, run, nodes, seed, rate = key
        tx = int(g["txPackets"].sum())
        rx = int(g["rxPackets"].sum())
        lost = int(g["lostPackets"].sum())
        offered = flows_configured * int(g["offeredPackets"].max())
        rx_bytes = int(g["rxBytes"].sum())
        # Janela útil lida dos dados (não de constante), para detectar erro no C++.
        useful_time = float(g["simTime"].iloc[0]) - float(g["appStart"].iloc[0])

        w_rx = g["rxPackets"].astype(float).to_numpy()
        delay = np.nan
        if w_rx.sum() > 0:
            delay = float(np.sum(g["delayMs"].to_numpy() * w_rx) / w_rx.sum())

        w_j = np.clip(g["rxPackets"].astype(float).to_numpy() - 1.0, 0.0, None)
        jitter = np.nan
        if w_j.sum() > 0:
            jitter = float(np.sum(g["jitterMs"].to_numpy() * w_j) / w_j.sum())

        rows.append(
            {
                "protocol": protocol,
                "speed": float(speed),
                "run": int(run),
                "nodes": int(nodes),
                "seed": int(seed),
                "rate": rate,
                "flows": int(len(g)),
                "flowsSemRecepcao": int((g["rxPackets"] == 0).sum()),
                "txPackets": tx,
                "rxPackets": rx,
                "lostPackets": lost,
                "offeredPackets": offered,
                "rxBytes": rx_bytes,
                "throughputMbps": (
                    8.0 * rx_bytes / (useful_time * 1e6) if useful_time > 0 else np.nan
                ),
                "pdrPct": 100.0 * rx / tx if tx > 0 else np.nan,
                "deliveryRatioPct": 100.0 * rx / offered if offered > 0 else np.nan,
                "delayMs": delay,
                "jitterMs": jitter,
            }
        )
    out = pd.DataFrame(rows)
    return out


def validate(
    df: pd.DataFrame, per_run: pd.DataFrame, name: str, expected_runs: int, var: str
) -> list[str]:
    """Retorna uma lista de linhas de relatório (checagens de sanidade)."""
    rep: list[str] = []
    problemas: list[str] = []
    rep.append(f"### {name}")
    rep.append("")
    rep.append(f"- Linhas brutas (fluxos) .............. {len(df)}")
    rep.append(f"- Execuções agregadas ................. {len(per_run)}")
    rep.append(f"- Protocolos .......................... {sorted(df['protocol'].unique())}")
    rep.append(f"- Valores da variável ({var}) ..... {sorted(df[var].unique())}")
    rep.append(f"- Runs por célula ..................... {sorted(df['run'].unique())}")
    n_flows_per_run = df.groupby(["protocol", var, "run"]).size()
    rep.append(
        f"- Fluxos por execução ................. "
        f"min={n_flows_per_run.min()} max={n_flows_per_run.max()} (esperado 4)"
    )
    # Fluxos não registrados pelo FlowMonitor (a origem não transmitiu).
    curtos = n_flows_per_run[n_flows_per_run < n_flows_per_run.max()]
    if len(curtos):
        problemas.append(
            f"{len(curtos)} execuções com menos fluxos observados que o configurado "
            "(total oferecido reconstruído): "
            + ", ".join(f"{p}/{v}/run{r}={n}" for (p, v, r), n in curtos.items())
        )
    n_runs = int(df["run"].nunique())
    per_cell = per_run.groupby(["protocol", var]).size()
    ok_cells = bool((per_cell == n_runs).all())
    rep.append(f"- {n_runs} runs em todas as células .......... {'OK' if ok_cells else 'FALHOU'}")
    rep.append(f"- Execuções esperadas ................. {expected_runs} / obtidas {len(per_run)}")

    # valores impossíveis
    for col, lo, hi in [
        ("pdrPct", 0.0, 100.0 + EPS),
        ("deliveryRatioPct", 0.0, 100.0 + 1e-3),
        ("throughputMbps", 0.0, float("inf")),
        ("delayMs", 0.0, float("inf")),
        ("jitterMs", 0.0, float("inf")),
    ]:
        s = df[col]
        bad = int(((s < lo - EPS) | (s > hi)).sum())
        if bad:
            problemas.append(f"{col}: {bad} valores fora de [{lo}, {hi}]")
    nan_cols = [c for c in df.columns if df[c].isna().any()]
    if nan_cols:
        problemas.append(f"colunas com NaN: {nan_cols}")

    # consistência tx <= offered (o OnOffApplication nunca oferece mais que a taxa)
    over = int((df["txPackets"] > df["offeredPackets"]).sum())
    if over:
        problemas.append(f"{over} fluxos com txPackets > offeredPackets")

    # fluxos sem recepção
    zero_rx = int((df["rxPackets"] == 0).sum())
    runs_zero = int((per_run["flowsSemRecepcao"] > 0).sum())
    rep.append(f"- Fluxos sem recepção (rx=0) .......... {zero_rx} (excluídos de atraso/jitter)")
    rep.append(f"- Execuções com ≥1 fluxo sem recepção . {runs_zero}")

    # offeredPackets deve ser constante por (rate, packetSize)
    off = df.groupby(["rate", "packetSize"])["offeredPackets"].nunique()
    if (off > 1).any():
        problemas.append(f"offeredPackets inconsistente: {off[off > 1].to_dict()}")

    # offeredPackets deve seguir taxa x janela útil / (pacote x 8).
    useful_time = float(df["simTime"].iloc[0]) - float(df["appStart"].iloc[0])
    packet_bits = float(df["packetSize"].iloc[0]) * 8.0

    def _bps(rate_label: object) -> float:
        s = str(rate_label).strip().lower()
        for suffix, mult in (("gbps", 1e9), ("mbps", 1e6), ("kbps", 1e3), ("bps", 1.0)):
            if s.endswith(suffix):
                try:
                    return float(s[: -len(suffix)]) * mult
                except ValueError:
                    return float("nan")
        return float("nan")

    for rate_label, got in df.groupby("rate")["offeredPackets"].first().items():
        expected = math.floor(_bps(rate_label) * useful_time / packet_bits)
        if int(got) != expected:
            problemas.append(
                f"offeredPackets para {rate_label}: obtido {int(got)}, esperado "
                f"{expected} (taxa x {useful_time:.0f}s / ({packet_bits:.0f} bits))"
            )

    rep.append(
        "- Pacotes oferecidos por fluxo ........ "
        + ", ".join(
            f"{r}={int(v)}"
            for r, v in df.groupby("rate")["offeredPackets"].first().items()
        )
    )

    # txPackets por protocolo (expõe o cache do OnOffApplication)
    txp = per_run.groupby("protocol")["txPackets"].mean()
    rep.append(
        "- txPackets médio por execução ........ "
        + ", ".join(f"{p}={v:.0f}" for p, v in txp.items())
    )

    if problemas:
        rep.append("")
        rep.append("**Problemas encontrados:**")
        for p in problemas:
            rep.append(f"- {p}")
    else:
        rep.append("")
        rep.append("**Nenhum problema de consistência encontrado.**")
    rep.append("")
    return rep


# ---------------------------------------------------------------------------
# Estatística
# ---------------------------------------------------------------------------
def summarize(per_run: pd.DataFrame, var: str) -> pd.DataFrame:
    """Resumo por (protocolo, valor da variável) para cada métrica."""
    rows = []
    for (proto, value), g in per_run.groupby(["protocol", var]):
        for col, label, unit, _ in METRICS:
            x = g[col].dropna().to_numpy(dtype=float)
            n = len(x)
            mean = float(np.mean(x)) if n else np.nan
            sd = float(np.std(x, ddof=1)) if n > 1 else float("nan")
            if n > 1:
                tcrit = float(stats.t.ppf(0.975, n - 1))
                half = tcrit * sd / math.sqrt(n)
            else:
                half = float("nan")
            rows.append(
                {
                    "protocol": proto,
                    var: value,
                    "metric": col,
                    "metricLabel": label,
                    "unit": unit,
                    "n": n,
                    "mean": mean,
                    "std": sd,
                    "min": float(np.min(x)) if n else np.nan,
                    "max": float(np.max(x)) if n else np.nan,
                    "ci95_low": mean - half if n > 1 else np.nan,
                    "ci95_high": mean + half if n > 1 else np.nan,
                    "ci95_half": half,
                }
            )
    return pd.DataFrame(rows)


def holm(pvals: list[float]) -> list[float]:
    """Correção de Holm-Bonferroni."""
    m = len(pvals)
    order = np.argsort(pvals)
    adjusted = [0.0] * m
    running = 0.0
    for rank, idx in enumerate(order):
        val = min(1.0, (m - rank) * pvals[idx])
        running = max(running, val)
        adjusted[idx] = running
    return adjusted


def kruskal_and_posthoc(per_run: pd.DataFrame, var: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    tests, posthoc = [], []
    for value, gv in per_run.groupby(var):
        for col, label, unit, _ in METRICS:
            groups = {
                p: g[col].dropna().to_numpy(dtype=float)
                for p, g in gv.groupby("protocol")
            }
            groups = {p: v for p, v in groups.items() if len(v) > 0}
            if len(groups) < 2:
                continue
            try:
                H, p = stats.kruskal(*groups.values())
            except ValueError:
                H, p = float("nan"), float("nan")
            tests.append(
                {
                    "variable": var,
                    "value": value,
                    "metric": col,
                    "metricLabel": label,
                    "unit": unit,
                    "H": float(H),
                    "p": float(p),
                    "df": len(groups) - 1,
                    "significant_0.05": bool(p < 0.05) if not math.isnan(p) else False,
                }
            )
            if not math.isnan(p) and p < 0.05:
                names = list(groups.keys())
                pairs, pvals = [], []
                for i in range(len(names)):
                    for j in range(i + 1, len(names)):
                        _, pij = stats.mannwhitneyu(
                            groups[names[i]], groups[names[j]], alternative="two-sided"
                        )
                        pairs.append((names[i], names[j]))
                        pvals.append(float(pij))
                adj = holm(pvals)
                for (a, b), pr, pa in zip(pairs, pvals, adj):
                    posthoc.append(
                        {
                            "variable": var,
                            "value": value,
                            "metric": col,
                            "metricLabel": label,
                            "group1": a,
                            "group2": b,
                            "p_raw": pr,
                            "p_holm": pa,
                            "significant_0.05": bool(pa < 0.05),
                        }
                    )
    tests_cols = [
        "variable", "value", "metric", "metricLabel", "unit",
        "H", "p", "df", "significant_0.05",
    ]
    posthoc_cols = [
        "variable", "value", "metric", "metricLabel",
        "group1", "group2", "p_raw", "p_holm", "significant_0.05",
    ]
    # Colunas explícitas: sem KW significativo, o pós-teste é vazio mas ainda
    # assim precisa de cabeçalho — um CSV de 0 bytes quebra pd.read_csv().
    return (
        pd.DataFrame(tests, columns=tests_cols),
        pd.DataFrame(posthoc, columns=posthoc_cols),
    )


def kruskal_by_factor(per_run: pd.DataFrame, var: str) -> pd.DataFrame:
    """Efeito do fator (velocidade ou taxa) dentro de cada protocolo e métrica.

    Complementa kruskal_and_posthoc, que compara os protocolos entre si em cada
    nível do fator.
    """
    rows = []
    for proto, gp in per_run.groupby("protocol"):
        for col, label, unit, _ in METRICS:
            groups = [
                g[col].dropna().to_numpy(dtype=float)
                for _, g in gp.groupby(var)
                if len(g[col].dropna()) > 0
            ]
            if len(groups) < 2 or min(len(g) for g in groups) < 1:
                continue
            try:
                H, p = stats.kruskal(*groups)
            except ValueError:
                H, p = float("nan"), float("nan")
            rows.append(
                {
                    "protocol": proto,
                    "factor": var,
                    "metric": col,
                    "metricLabel": label,
                    "unit": unit,
                    "n_levels": len(groups),
                    "H": float(H),
                    "p": float(p),
                    "df": len(groups) - 1,
                    "significant_0.05": bool(p < 0.05) if not math.isnan(p) else False,
                }
            )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def process(raw: Path, processed: Path, stem: str, var: str, report: list[str]):
    src = raw / f"results_{stem}.csv"
    df = load_raw(src)
    per_run = aggregate_per_run(df)
    summary = summarize(per_run, var)
    tests, posthoc = kruskal_and_posthoc(per_run, var)

    n_runs = int(df["run"].nunique())
    expected_runs = int(df["protocol"].nunique() * df[var].nunique() * n_runs)

    per_run.to_csv(processed / f"per_run_{stem}.csv", index=False)
    summary.to_csv(processed / f"summary_{stem}.csv", index=False)
    tests.to_csv(processed / f"tests_{stem}.csv", index=False)
    posthoc.to_csv(processed / f"posthoc_{stem}.csv", index=False)

    titulo = "velocidade (m/s)" if var == "speed" else "taxa por fluxo"

    effects = kruskal_by_factor(per_run, var)
    effects.to_csv(processed / f"efeito_{stem}.csv", index=False)

    report.append(f"## Experimento: {stem} (variável = {titulo})")
    report.append("")
    report += validate(df, per_run, f"Validação — {stem}", expected_runs, var)
    return per_run, summary, tests, posthoc, effects


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--processed", default="data/processed")
    args = ap.parse_args()

    raw, processed = Path(args.raw), Path(args.processed)
    processed.mkdir(parents=True, exist_ok=True)

    report = ["# Relatório de análise — MANET + ns-3", ""]
    report.append(
        "Gerado por `scripts/analyze.py` a partir dos CSVs brutos em `data/raw/`."
    )
    report.append("")

    results = {}
    have_base = (raw / "results_base.csv").exists()
    have_rate = (raw / "results_rate.csv").exists()
    if have_base:
        results["base"] = process(raw, processed, "base", "speed", report)
    if have_rate:
        results["rate"] = process(raw, processed, "rate", "rate", report)
    if not results:
        print("ERRO: nenhum CSV bruto encontrado em", raw)
        return 1

    # Dados desbalanceados (lote incompleto) abortam a análise.
    problemas_estruturais: list[str] = []
    for stem, res in results.items():
        var = "speed" if stem == "base" else "rate"
        per_cell = res[0].groupby(["protocol", var]).size()
        if per_cell.nunique() > 1:
            detalhe = ", ".join(f"{p}/{v}: {n}" for (p, v), n in per_cell.items())
            problemas_estruturais.append(
                f"[{stem}] células com número diferente de execuções -> {detalhe}"
            )
    if problemas_estruturais:
        print("ERRO: dados desbalanceados (lote incompleto?). Análise abortada.")
        for p in problemas_estruturais:
            print("  -", p)
        return 1

    # ------------------------------------------------------------------
    # Síntese
    # ------------------------------------------------------------------
    report.append("## Síntese")
    report.append("")
    if "base" in results:
        _, summary, tests, posthoc, effects = results["base"]
        for col, label, unit, lower_better in METRICS:
            sub = summary[summary["metric"] == col]
            best = {}
            for value in SPEED_ORDER:
                sv = sub[sub["speed"] == value]
                if sv.empty:
                    continue
                idx = sv["mean"].idxmin() if lower_better else sv["mean"].idxmax()
                best[value] = (sv.loc[idx, "protocol"], sv.loc[idx, "mean"])
            report.append(
                f"- **{label} ({unit})** — melhor protocolo por velocidade: "
                + "; ".join(f"{s} m/s: {p} ({m:.2f})" for s, (p, m) in best.items())
            )
        sig = tests[tests["significant_0.05"]]
        report.append("")
        report.append(
            f"- Kruskal–Wallis: {len(sig)} de {len(tests)} combinações "
            "(velocidade × métrica) com diferença significativa (p < 0,05)."
        )
        for _, r in sig.iterrows():
            ph = posthoc[
                (posthoc["value"] == r["value"]) & (posthoc["metric"] == r["metric"])
            ]
            pares = ", ".join(
                f"{x['group1']}≠{x['group2']} (p={x['p_holm']:.3f})"
                for _, x in ph.iterrows()
                if x["significant_0.05"]
            )
            report.append(
                f"  - {r['metricLabel']} @ {r['value']:g} m/s: H={r['H']:.2f}, "
                f"p={r['p']:.4f}" + (f" — {pares}" if pares else "")
            )
    if "rate" in results:
        _, summary, tests, posthoc, effects = results["rate"]
        report.append("")
        for col, label, unit, lower_better in METRICS:
            sub = summary[summary["metric"] == col]
            best = {}
            for value in RATE_ORDER:
                sv = sub[sub["rate"] == value]
                if sv.empty:
                    continue
                idx = sv["mean"].idxmin() if lower_better else sv["mean"].idxmax()
                best[value] = (sv.loc[idx, "protocol"], sv.loc[idx, "mean"])
            report.append(
                f"- **{label} ({unit})** — melhor protocolo por taxa: "
                + "; ".join(f"{s}: {p} ({m:.2f})" for s, (p, m) in best.items())
            )
        sig = tests[tests["significant_0.05"]]
        report.append("")
        report.append(
            f"- Kruskal–Wallis (taxa): {len(sig)} de {len(tests)} combinações com "
            "diferença significativa (p < 0,05)."
        )

    report.append("")
    report.append("### Efeito do fator dentro de cada protocolo (Kruskal–Wallis)")
    report.append("")
    report.append(
        "Testa se a velocidade (experimento `base`) ou a taxa (`rate`) altera a "
        "métrica **dentro** de cada protocolo — pergunta distinta de "
        "\"os protocolos diferem entre si em um dado nível do fator?\"."
    )
    report.append("")
    for stem, res in results.items():
        effects = res[4]
        for _, r in effects.iterrows():
            estado = "significativo" if r["significant_0.05"] else "não significativo"
            report.append(
                f"- [{stem}] {r['protocol']} — {r['metricLabel']}: "
                f"H={r['H']:.2f}, p={r['p']:.4f} ({estado})"
            )

    (processed / "relatorio_analise.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    # ------------------------------------------------------------------
    # Saída no terminal
    # ------------------------------------------------------------------
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 50)
    var_of = {"base": "speed", "rate": "rate"}
    for stem, (per_run, summary, tests, posthoc, effects) in results.items():
        var = var_of[stem]
        print(f"\n===== {stem} (variável: {var}) =====")
        print(f"execuções: {len(per_run)}")
        for col, label, unit, _ in METRICS:
            print(f"\n-- {label} ({unit}) --")
            sub = summary[summary["metric"] == col]
            piv = sub.pivot_table(index="protocol", columns=var, values="mean")
            print(piv.round(3))
    print("\nArquivos gravados em:", processed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
