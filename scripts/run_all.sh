#!/usr/bin/env bash
#
# run_all.sh — executa a matriz experimental e consolida os CSVs brutos.
#
#   base: 3 protocolos x 4 velocidades (1, 5, 10, 20 m/s) x RUNS
#   rate: 3 protocolos x 4 taxas (256kbps, 512kbps, 1Mbps, 2Mbps) x RUNS,
#         com velocidade fixa em 10 m/s
#
# Cada execução grava um parcial em data/raw/parts/; ao final os parciais são
# unidos em data/raw/results_base.csv e data/raw/results_rate.csv. Execuções
# já concluídas são reaproveitadas (FORCE=1 refaz tudo).
#
# Uso:
#   ./scripts/run_all.sh                 # todos os núcleos disponíveis
#   JOBS=2 ./scripts/run_all.sh          # limita o paralelismo
#   NS3_DIR=/caminho/ns-3.48 ./scripts/run_all.sh
#   MODE=base ./scripts/run_all.sh       # só a matriz base
#   MODE=rate ./scripts/run_all.sh       # só a variável adicional
#   RUNS=5 ./scripts/run_all.sh          # número de repetições
#
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# ns-3 como diretório irmão por padrão; sobrescreva com NS3_DIR.
NS3_DIR="${NS3_DIR:-$REPO_DIR/../ns-3.48}"
PROG="manet-routing"
MODE="${MODE:-all}"
JOBS="${JOBS:-$(nproc)}"
SEED="${SEED:-12345}"
RUNS="${RUNS:-30}"

# --- velocidades e taxas das duas matrizes -----------------------------------
SPEEDS=(1 5 10 20)                       # m/s  (matriz base)
RATES=("256kbps" "512kbps" "1Mbps" "2Mbps")  # por fluxo (variável adicional)
RATE_SPEED=10                            # m/s  (velocidade fixa da variável adicional)
PROTOCOLS=(AODV OLSR DSDV)

# --- parâmetros fixos do cenário --------------------------------------------
NODES=20
FLOWS=4
PACKET_SIZE=1024
SIM_TIME=120
APP_START=10
AREA=500
TX_POWER=7.5
PAUSE=0

RAW_DIR="$REPO_DIR/data/raw"
PARTS_DIR="$RAW_DIR/parts"
LOGS_DIR="$RAW_DIR/logs"
JOBFILE="$RAW_DIR/jobs.txt"

# --- localiza o binário compilado -------------------------------------------
# Executar o binário direto evita disputa do build do ns-3 entre processos.
BIN="$(find "$NS3_DIR/build/scratch" -maxdepth 1 -type f -name "ns3.*-${PROG}-default" 2>/dev/null | head -n1 || true)"
if [[ -z "$BIN" || ! -x "$BIN" ]]; then
    echo "ERRO: binário '$PROG' não encontrado em $NS3_DIR/build/scratch/." >&2
    echo "Execute antes:  ./scripts/setup.sh" >&2
    exit 1
fi

echo "==> Repositório : $REPO_DIR"
echo "==> ns-3        : $NS3_DIR"
echo "==> Binário     : $BIN"
echo "==> Paralelismo : $JOBS processo(s)"
echo "==> Modo        : $MODE"

# Um parcial já completo é reaproveitado.
if [[ "${FORCE:-0}" == "1" ]]; then
    rm -rf "$PARTS_DIR" "$LOGS_DIR"
fi
mkdir -p "$PARTS_DIR" "$LOGS_DIR"

# --- gera a lista de tarefas -------------------------------------------------
# Campos: tag protocolo velocidade run taxa nós área
: > "$JOBFILE"
if [[ "$MODE" == "all" || "$MODE" == "base" ]]; then
    for proto in "${PROTOCOLS[@]}"; do
        for speed in "${SPEEDS[@]}"; do
            for run in $(seq 1 "$RUNS"); do
                echo "base_${proto}_${speed}_${run} $proto $speed $run 256kbps $NODES $AREA" >> "$JOBFILE"
            done
        done
    done
fi
if [[ "$MODE" == "all" || "$MODE" == "rate" ]]; then
    for proto in "${PROTOCOLS[@]}"; do
        for rate in "${RATES[@]}"; do
            for run in $(seq 1 "$RUNS"); do
                echo "rate_${proto}_${rate}_${run} $proto $RATE_SPEED $run $rate $NODES $AREA" >> "$JOBFILE"
            done
        done
    done
fi

TOTAL="$(wc -l < "$JOBFILE")"
echo "==> Tarefas     : $TOTAL execuções"
echo

# --- uma execução ------------------------------------------------------------
run_one() {
    local tag="$1" proto="$2" speed="$3" run="$4" rate="$5" nodes="$6" area="$7"
    local part="$PARTS_DIR/${tag}.csv"
    local log="$LOGS_DIR/${tag}.log"
    # Reaproveita parcial já completo (cabeçalho + FLOWS linhas).
    if [[ -s "$part" && "$(wc -l < "$part")" -eq $((FLOWS + 1)) ]]; then
        return 0
    fi
    "$BIN" \
        --protocol="$proto" \
        --speed="$speed" \
        --run="$run" \
        --rate="$rate" \
        --nodes="$nodes" \
        --area="$area" \
        --pause="$PAUSE" \
        --flows="$FLOWS" \
        --packetSize="$PACKET_SIZE" \
        --simTime="$SIM_TIME" \
        --appStart="$APP_START" \
        --txPower="$TX_POWER" \
        --seed="$SEED" \
        --outCsv="$part" > "$log" 2>&1
}
export -f run_one
export BIN PARTS_DIR LOGS_DIR PAUSE FLOWS PACKET_SIZE SIM_TIME APP_START TX_POWER SEED

# --- executa em paralelo -----------------------------------------------------
START_TS="$(date +%s)"
if ! xargs -P "$JOBS" -n 7 -a "$JOBFILE" bash -c 'set -euo pipefail; run_one "$@"' _ ; then
    echo "ERRO: pelo menos uma execução falhou. Verifique $LOGS_DIR/" >&2
    exit 1
fi
END_TS="$(date +%s)"

# --- valida a saída de cada execução ----------------------------------------
missing=0
for tag in $(awk '{print $1}' "$JOBFILE"); do
    part="$PARTS_DIR/${tag}.csv"
    if [[ ! -s "$part" ]]; then
        echo "ERRO: parcial ausente/vazio: $part" >&2
        missing=$((missing + 1))
        continue
    fi
    # cada execução válida exporta exatamente FLOWS linhas de dados (+ cabeçalho)
    lines="$(wc -l < "$part")"
    if [[ "$lines" -ne $((FLOWS + 1)) ]]; then
        echo "AVISO: $part tem $lines linhas (esperado $((FLOWS + 1)))" >&2
    fi
done
if [[ "$missing" -gt 0 ]]; then
    echo "ERRO: $missing execuções sem saída." >&2
    exit 1
fi

# --- une os parciais na ordem canônica --------------------------------------
merge_parts() {
    local out="$1"
    shift
    local first=1
    : > "$out"
    for part in "$@"; do
        if [[ "$first" -eq 1 ]]; then
            cat "$part" >> "$out"
            first=0
        else
            tail -n +2 "$part" >> "$out"
        fi
    done
}

if [[ "$MODE" == "all" || "$MODE" == "base" ]]; then
    mapfile -t base_parts < <(awk '$1 ~ /^base_/ {print "'"$PARTS_DIR"'/" $1 ".csv"}' "$JOBFILE")
    merge_parts "$RAW_DIR/results_base.csv" "${base_parts[@]}"
    echo "==> $RAW_DIR/results_base.csv ($(($(wc -l < "$RAW_DIR/results_base.csv") - 1)) linhas de dados)"
fi
if [[ "$MODE" == "all" || "$MODE" == "rate" ]]; then
    mapfile -t rate_parts < <(awk '$1 ~ /^rate_/ {print "'"$PARTS_DIR"'/" $1 ".csv"}' "$JOBFILE")
    merge_parts "$RAW_DIR/results_rate.csv" "${rate_parts[@]}"
    echo "==> $RAW_DIR/results_rate.csv ($(($(wc -l < "$RAW_DIR/results_rate.csv") - 1)) linhas de dados)"
fi

# --- registra os comandos exatos --------------------------------------------
{
    echo "# Comandos executados por run_all.sh"
    echo "# data: $(date -Iseconds)"
    echo "# binario: $BIN"
    echo "# parametros fixos: pause=$PAUSE flows=$FLOWS packetSize=$PACKET_SIZE simTime=$SIM_TIME appStart=$APP_START txPower=$TX_POWER seed=$SEED runs=$RUNS"
    echo
    while read -r tag proto speed run rate nodes area; do
        echo "$BIN --protocol=$proto --speed=$speed --run=$run --rate=$rate --nodes=$nodes --area=$area --pause=$PAUSE --flows=$FLOWS --packetSize=$PACKET_SIZE --simTime=$SIM_TIME --appStart=$APP_START --txPower=$TX_POWER --seed=$SEED --outCsv=<part>"
    done < "$JOBFILE"
} > "$RAW_DIR/commands.txt"

echo
echo "==> Concluído em $((END_TS - START_TS)) s ($TOTAL execuções, $JOBS em paralelo)"
echo "==> Parciais: $PARTS_DIR/  |  Logs: $LOGS_DIR/  |  Comandos: $RAW_DIR/commands.txt"
