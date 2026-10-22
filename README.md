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

## Requisitos

- Ubuntu 24.04 (ou distribuição equivalente com `apt`)
- ns-3.48, instalado conforme o passo 1 abaixo (o simulador não é versionado neste repositório)
- Python 3 (as bibliotecas estão listadas em `requirements.txt`)

## Organização das pastas

O ns-3 e este repositório ficam lado a lado em uma mesma pasta de trabalho
(aqui chamada `trabalho-redes/`, mas o nome é livre). Ao final da instalação:

```
trabalho-redes/
├── ns-allinone-3.48/
│   └── ns-3.48/          # simulador compilado (NS3_DIR aponta para cá)
├── ns-allinone-3.48.tar.bz2
└── manet-ns3/            # este repositório
```

Os scripts localizam o ns-3 pela variável de ambiente `NS3_DIR`, definida no passo 2.

## Instalação

### 1. Instalar e compilar o ns-3.48

📁 **Pasta:** `trabalho-redes/`

Instale as dependências do sistema:

```bash
sudo apt update
sudo apt install g++ cmake python3 python3-pip python3-venv git wget
```

Baixe, extraia e compile o ns-3:

```bash
wget https://www.nsnam.org/releases/ns-allinone-3.48.tar.bz2
tar xjf ns-allinone-3.48.tar.bz2
cd ns-allinone-3.48/ns-3.48
./ns3 configure
./ns3 build
cd ../..
```

A compilação leva vários minutos. O último `cd` retorna para `trabalho-redes/`.

### 2. Clonar o repositório e definir `NS3_DIR`

📁 **Pasta:** `trabalho-redes/`

```bash
git clone https://github.com/USUARIO/REPOSITORIO.git manet-ns3
export NS3_DIR=$(pwd)/ns-allinone-3.48/ns-3.48
```

Confira se o caminho está correto (deve listar o arquivo `ns3`):

```bash
ls $NS3_DIR/ns3
```

O `export` vale apenas para o terminal atual. Para não precisar repeti-lo a cada
novo terminal, grave-o no `~/.bashrc` (ainda em `trabalho-redes/`):

```bash
echo "export NS3_DIR=$(pwd)/ns-allinone-3.48/ns-3.48" >> ~/.bashrc
```

### 3. Criar o ambiente Python

📁 **Pasta:** `trabalho-redes/manet-ns3/`

```bash
cd manet-ns3
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

O ambiente precisa ser ativado (`source .venv/bin/activate`) a cada novo
terminal antes de executar os scripts Python.

### 4. Compilar o programa de simulação

📁 **Pasta:** `trabalho-redes/manet-ns3/`

```bash
./scripts/setup.sh
```

O script copia `src/manet-routing.cc` para a pasta `scratch/` do ns-3 e o
compila.

## Execução

Todos os comandos desta seção partem de `trabalho-redes/manet-ns3/`, com
`NS3_DIR` definida.

### 1. Testar uma execução isolada

Antes do lote completo, confirme que a simulação funciona com uma única execução:

```bash
mkdir -p data/raw
cd "$NS3_DIR"
./ns3 run "scratch/manet-routing \
  --protocol=AODV --speed=10 --run=1 --nodes=20 --flows=4 \
  --packetSize=1024 --rate=256kbps --simTime=120 --appStart=10 \
  --seed=12345 --outCsv=$OLDPWD/data/raw/smoke.csv"
cd -
```

O comando entra temporariamente na pasta do ns-3 (de onde o `./ns3` precisa ser
executado), roda a simulação e volta para `manet-ns3/` com o `cd -`. A variável
`$OLDPWD` faz o CSV de saída ser gravado em `manet-ns3/data/raw/smoke.csv`.

A saída esperada é:

```
[CONFIG]  protocol=AODV speed=10 ...
[ROUTING] instalado=ns3::aodv::RoutingProtocol nos=20
[RESULT]  protocol=AODV speed=10 run=1 nodes=20 flowsExportados=4 tx=... rx=... pdrAgregado=...%
[OUTPUT]  .../data/raw/smoke.csv
```

A linha `[ROUTING]` confirma o protocolo instalado, e `flowsExportados=4`
indica que os quatro fluxos foram medidos.

### 2. Rodar o lote completo

O repositório já inclui os resultados parciais das 720 execuções em
`data/raw/parts/`. Como o lote é retomável (execuções já concluídas são
reaproveitadas), rodar `./scripts/run_all.sh` sem opções apenas consolida os
CSVs, em poucos segundos. Para reproduzir todas as simulações do zero, use
`FORCE=1`:

```bash
FORCE=1 ./scripts/run_all.sh
```

O script usa todos os núcleos disponíveis; com 4 núcleos, o lote completo leva
cerca de 40 minutos. Durante a execução não há saída no terminal, pois cada
simulação grava seu log em arquivo. Para acompanhar o andamento, abra um segundo
terminal em `manet-ns3/` e conte os parciais concluídos (total de 720):

```bash
watch -n 5 'ls data/raw/parts | wc -l'
```

Opções disponíveis (use uma por vez, combinadas com `FORCE=1` quando quiser
refazer as execuções):

| Variável | Efeito |
|---|---|
| `JOBS=2` | limita o número de processos em paralelo |
| `MODE=base` | executa só a matriz base (360 execuções) |
| `MODE=rate` | executa só a variável adicional (360 execuções) |
| `RUNS=5` | reduz o número de repetições por configuração |
| `FORCE=1` | apaga os parciais e logs existentes e refaz tudo |

Exemplo: `FORCE=1 JOBS=4 ./scripts/run_all.sh`.

Ao final, o lote consolida os resultados em `data/raw/results_base.csv` e
`data/raw/results_rate.csv`, mantém um parcial por execução em
`data/raw/parts/`, os logs em `data/raw/logs/` e os comandos exatos em
`data/raw/commands.txt`.

### 3. Analisar e gerar figuras

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
- Os três protocolos usam a mesma faixa de runs (1 a 30).
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

- **Propagação idealizada.** O `FriisPropagationLossModel` é fixado em 2,412 GHz
  (canal 1 do 802.11b) e o alcance resultante, ~295 m, é limitado pelo
  `ThresholdPreambleDetectionModel` do ns-3 e não pelo piso de ruído. Como a área
  é 500 × 500 m, a comunicação exige encaminhamento multi-salto, e algumas
  distribuições de nós podem deixar pares origem-destino temporariamente sem
  caminho. O cenário mede o efeito da mobilidade sobre a validade das rotas e a
  contenção.
- **Velocidade constante por nó** e pause time zero.
- **Uma única seed mestre**, com a variação entre execuções vindo do `run`.
- **Vazão medida na camada de rede** (datagrama IP), ligeiramente acima do
  _goodput_ de aplicação.
- Não são avaliados consumo de energia, escalabilidade com muitos nós nem
  tráfego TCP.

## Licença

GPL-2.0, a mesma do ns-3. Derivado do exemplo `examples/routing/manet-routing-compare.cc`.
