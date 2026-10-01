#!/usr/bin/env bash
#
# setup.sh — copia src/manet-routing.cc para o scratch/ do ns-3 e compila.
#
# Uso:
#   ./scripts/setup.sh
#   NS3_DIR=/caminho/para/ns-3.48 ./scripts/setup.sh
#
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# ns-3 como diretório irmão por padrão; sobrescreva com NS3_DIR.
NS3_DIR="${NS3_DIR:-$REPO_DIR/../ns-3.48}"

if [[ ! -x "$NS3_DIR/ns3" ]]; then
    echo "ERRO: script 'ns3' nao encontrado em $NS3_DIR" >&2
    echo "Defina NS3_DIR apontando para a raiz da instalacao do ns-3." >&2
    exit 1
fi

echo "==> Repositorio : $REPO_DIR"
echo "==> ns-3        : $NS3_DIR"

mkdir -p "$NS3_DIR/scratch"
install -m 644 "$REPO_DIR/src/manet-routing.cc" "$NS3_DIR/scratch/manet-routing.cc"
echo "==> Copiado: src/manet-routing.cc -> $NS3_DIR/scratch/manet-routing.cc"

cd "$NS3_DIR"
echo "==> Compilando (build incremental)"
./ns3 build

echo
echo "Pronto. Teste rapido:"
echo "  cd $NS3_DIR"
echo "  ./ns3 run \"scratch/manet-routing --protocol=AODV --speed=10 --run=1 --outCsv=$REPO_DIR/data/raw/smoke.csv\""
