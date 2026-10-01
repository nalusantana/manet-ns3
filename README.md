# MANET + ns-3 — mobilidade em AODV, OLSR e DSDV

Simulação de uma rede móvel _ad hoc_ (MANET) IEEE 802.11 em modo Ad Hoc no
ns-3.48, medindo o efeito da velocidade dos nós e da taxa de transmissão sobre
os protocolos AODV, OLSR e DSDV.

- **Matriz base:** 3 protocolos × 4 velocidades (1, 5, 10, 20 m/s) × 30
  repetições = 360 execuções.
- **Variável adicional:** 3 protocolos × 4 taxas por fluxo (256 kbps, 512 kbps,
  1 Mbps, 2 Mbps) × 30 repetições a 10 m/s = 360 execuções.
- **Total:** 720 execuções.

Resultados, testes estatísticos e médias estão em
`data/processed/relatorio_analise.md` e nos CSVs de `data/processed/`.

## Requisitos

- ns-3.48 compilado (`./ns3 build`); o simulador não é versionado neste
  repositório.
- Python 3 com `pandas`, `numpy`, `scipy` e `matplotlib`:

```bash
python3 -m pip install pandas numpy scipy matplotlib
```

## Estrutura

```
manet-ns3/
├── src/manet-routing.cc        # programa de simulação (parametrizável por CLI)
├── scripts/
│   ├── setup.sh                # copia o programa para o scratch/ do ns-3 e compila
│   ├── run_all.sh              # executa a matriz completa -> data/raw/
│   ├── run_batch.sh            # wrapper de run_all.sh
│   ├── analyze.py              # validação, agregação e estatística -> data/processed/
│   └── plot.py                 # figuras -> figures/
├── data/
│   ├── raw/                    # CSVs brutos, parciais por execução e logs
│   └── processed/              # agregados, testes e relatório
└── figures/                    # figuras em PDF e PNG (300 dpi)
```

## Uso

### 1. Compilar o programa dentro do ns-3

```bash
./scripts/setup.sh
```

`NS3_DIR` aponta para o ns-3; por padrão assume que ele é diretório irmão de
`manet-ns3/`.

### 2. Rodar um cenário isolado

```bash
cd "$NS3_DIR"
./ns3 run "scratch/manet-routing \
  --protocol=AODV --speed=10 --run=1 --nodes=20 --flows=4 \
  --packetSize=1024 --rate=256kbps --simTime=120 --appStart=10 \
  --seed=12345 --outCsv=$OLDPWD/data/raw/smoke.csv"
```

O programa imprime a configuração, a autoverificação do protocolo instalado e o
resumo da execução:

```
[CONFIG]  protocol=AODV speed=10 ...
[ROUTING] instalado=ns3::aodv::RoutingProtocol nos=20
[RESULT]  protocol=AODV speed=10 run=1 nodes=20 flowsExportados=4 tx=... rx=... pdrAgregado=...%
[OUTPUT]  .../data/raw/smoke.csv
```

### 3. Rodar o lote completo

```bash
./scripts/run_all.sh            # ~40 min em 4 núcleos; retomável
JOBS=2 ./scripts/run_all.sh     # limita o paralelismo
MODE=base ./scripts/run_all.sh  # só a matriz base (360 execuções)
MODE=rate ./scripts/run_all.sh  # só a variável adicional (360 execuções)
RUNS=5 ./scripts/run_all.sh     # menos repetições
FORCE=1 ./scripts/run_all.sh    # ignora parciais e refaz tudo
```

O lote escreve um parcial por execução em `data/raw/parts/`, o log em
`data/raw/logs/` e consolida tudo em `data/raw/results_base.csv` e
`data/raw/results_rate.csv`. Os comandos exatos ficam em
`data/raw/commands.txt`.

### 4. Analisar e gerar figuras

```bash
python3 scripts/analyze.py
python3 scripts/plot.py
```

`analyze.py` grava em `data/processed/`: `per_run_*.csv`, `summary_*.csv`
(média, desvio-padrão e IC 95%), `tests_*.csv` (Kruskal-Wallis), `posthoc_*.csv`
(Mann-Whitney com correção de Holm), `efeito_*.csv` e `relatorio_analise.md`.
`plot.py` grava 12 figuras em `figures/` (PDF e PNG 300 dpi).

## Parâmetros do programa

| Parâmetro | Significado | Unidade | Padrão |
|---|---|---|---|
| `--protocol` | Protocolo de roteamento: `AODV`, `OLSR` ou `DSDV` | — | `AODV` |
| `--speed` | Velocidade (constante) de cada nó no Random Waypoint | m/s | `10` |
| `--pause` | Tempo de pausa do Random Waypoint | s | `0` |
| `--area` | Lado da área quadrada de posicionamento | m | `500` |
| `--nodes` | Número de nós | — | `20` |
| `--flows` | Número de fluxos UDP simultâneos | — | `4` |
| `--packetSize` | Tamanho do pacote UDP | bytes | `1024` |
| `--rate` | Taxa oferecida por fluxo (ex.: `256kbps`, `1Mbps`) | — | `256kbps` |
| `--simTime` | Duração total da simulação | s | `120` |
| `--appStart` | Início do tráfego UDP | s | `10` |
| `--txPower` | Potência de transmissão (início e fim) | dBm | `7.5` |
| `--run` | Número da execução / repetição | — | `1` |
| `--seed` | Seed mestre do gerador aleatório | — | `12345` |
| `--outCsv` | Arquivo CSV de saída (modo _append_) | — | `manet-results.csv` |
| `--verbose` | Imprime a configuração detalhada dos fluxos | — | `false` |

## Cenário

| Parâmetro | Valor |
|---|---|
| Nós | 20 |
| Área | 500 × 500 m (`RandomRectanglePositionAllocator`) |
| Mobilidade | `RandomWaypointMobilityModel`, pause 0 s, velocidade constante |
| Wi-Fi | 802.11b ad hoc (`AdhocWifiMac`), dados a 11 Mbps, controle a 1 Mbps |
| Canal | `YansWifiChannel` + `FriisPropagationLossModel` + `ConstantSpeedPropagationDelayModel` |
| Potência TX | 7,5 dBm |
| Aplicação | UDP CBR (`OnOffApplication`, `OnTime=1`, `OffTime=0`) |
| Fluxos | 4, pareados 0→19, 1→18, 2→17, 3→16 (portas 9000..9003) |
| Tráfego | inicia em t = 10 s e termina em t = 120 s |

## Métricas (via `FlowMonitor`)

| Métrica | Fórmula | Unidade |
|---|---|---|
| Throughput | `rxBytes × 8 / (simTime − appStart) / 1e6` | Mbps |
| PDR | `rxPackets / txPackets × 100` | % |
| Razão de entrega | `rxPackets / offeredPackets × 100` | % |
| Atraso médio | `delaySum / rxPackets × 1000` | ms |
| Jitter médio | `jitterSum / (rxPackets − 1) × 1000` | ms |

Notas:

- O denominador do throughput é a janela útil de tráfego (`simTime − appStart`),
  não o tempo total da simulação.
- São reportadas duas razões de entrega. O `OnOffApplication` guarda em cache o
  pacote que falhou por ausência de rota e o retenta no intervalo seguinte; nesses
  intervalos o `txPackets` do FlowMonitor fica menor que o total oferecido, de
  forma desigual entre os protocolos. `pdrPct` usa o denominador do FlowMonitor e
  `deliveryRatioPct` usa o total calculado a partir da taxa configurada.
- Apenas os fluxos de dados são contabilizados. O tráfego de controle (AODV 654,
  OLSR 698, DSDV 2009) é filtrado.
- Fluxos com `rxPackets == 0` são registrados, mas excluídos do cálculo de atraso
  e jitter.

## Reprodutibilidade

- Seed mestre fixa (`RngSeedManager::SetSeed(12345)`).
- Repetições independentes via `RngSeedManager::SetRun(run)` com `run = 1..30`.
- Os três protocolos usam a mesma faixa de runs, de modo que cada um enfrenta as
  mesmas posições, velocidades e destinos.
- Cada execução é uma amostra independente; as métricas são agregadas dentro da
  execução (somando/ponderando os 4 fluxos) e depois resumidas entre execuções.
- IC 95% por t-Student e comparação entre protocolos por Kruskal-Wallis, com
  Mann-Whitney par a par e correção de Holm quando p < 0,05.

## Saídas

| Saída | Caminho |
|---|---|
| Parciais por execução | `data/raw/parts/*.csv` |
| CSV bruto consolidado | `data/raw/results_base.csv`, `data/raw/results_rate.csv` |
| Comandos do lote | `data/raw/commands.txt` |
| Logs por execução | `data/raw/logs/*.log` |
| Métricas por execução | `data/processed/per_run_*.csv` |
| Resumo com IC 95% | `data/processed/summary_*.csv` |
| Testes estatísticos | `data/processed/tests_*.csv`, `posthoc_*.csv`, `efeito_*.csv` |
| Relatório | `data/processed/relatorio_analise.md` |
| Figuras | `figures/*.pdf`, `figures/*.png` |

## Limitações

- **Propagação idealizada.** Com `FriisPropagationLossModel` e 7,5 dBm o alcance
  efetivo supera os 500 m da área, de modo que os 20 nós compartilham um único
  domínio de colisão. O cenário mede principalmente o efeito da mobilidade sobre
  a contenção e a validade das rotas.
- **Velocidade constante por nó** e pause time zero.
- **Uma única seed mestre**, com a variação entre execuções vindo do `run`.
- **Vazão medida na camada de rede** (datagrama IP), ligeiramente acima do
  _goodput_ de aplicação.
- Não são avaliados consumo de energia, escalabilidade com muitos nós nem
  tráfego TCP.

## Licença

GPL-2.0, a mesma do ns-3. Derivado do exemplo `examples/routing/manet-routing-compare.cc`.
