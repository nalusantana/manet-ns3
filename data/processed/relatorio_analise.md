# Relatório de análise — MANET + ns-3

Gerado por `scripts/analyze.py` a partir dos CSVs brutos em `data/raw/`.

## Experimento: base (variável = velocidade (m/s))

### Validação — base

- Linhas brutas (fluxos) .............. 1440
- Execuções agregadas ................. 360
- Protocolos .......................... ['AODV', 'DSDV', 'OLSR']
- Valores da variável (speed) ..... [np.float64(1.0), np.float64(5.0), np.float64(10.0), np.float64(20.0)]
- Runs por célula ..................... [np.int64(1), np.int64(2), np.int64(3), np.int64(4), np.int64(5), np.int64(6), np.int64(7), np.int64(8), np.int64(9), np.int64(10), np.int64(11), np.int64(12), np.int64(13), np.int64(14), np.int64(15), np.int64(16), np.int64(17), np.int64(18), np.int64(19), np.int64(20), np.int64(21), np.int64(22), np.int64(23), np.int64(24), np.int64(25), np.int64(26), np.int64(27), np.int64(28), np.int64(29), np.int64(30)]
- Fluxos por execução ................. min=4 max=4 (esperado 4)
- 30 runs em todas as células .......... OK
- Execuções esperadas ................. 360 / obtidas 360
- Fluxos sem recepção (rx=0) .......... 6 (excluídos de atraso/jitter)
- Execuções com ≥1 fluxo sem recepção . 5
- Pacotes oferecidos por fluxo ........ 256kbps=3437
- txPackets médio por execução ........ AODV=13748, DSDV=13748, OLSR=13743

**Nenhum problema de consistência encontrado.**

## Experimento: rate (variável = taxa por fluxo)

### Validação — rate

- Linhas brutas (fluxos) .............. 1440
- Execuções agregadas ................. 360
- Protocolos .......................... ['AODV', 'DSDV', 'OLSR']
- Valores da variável (rate) ..... ['1Mbps', '256kbps', '2Mbps', '512kbps']
- Runs por célula ..................... [np.int64(1), np.int64(2), np.int64(3), np.int64(4), np.int64(5), np.int64(6), np.int64(7), np.int64(8), np.int64(9), np.int64(10), np.int64(11), np.int64(12), np.int64(13), np.int64(14), np.int64(15), np.int64(16), np.int64(17), np.int64(18), np.int64(19), np.int64(20), np.int64(21), np.int64(22), np.int64(23), np.int64(24), np.int64(25), np.int64(26), np.int64(27), np.int64(28), np.int64(29), np.int64(30)]
- Fluxos por execução ................. min=4 max=4 (esperado 4)
- 30 runs em todas as células .......... OK
- Execuções esperadas ................. 360 / obtidas 360
- Fluxos sem recepção (rx=0) .......... 6 (excluídos de atraso/jitter)
- Execuções com ≥1 fluxo sem recepção . 6
- Pacotes oferecidos por fluxo ........ 1Mbps=13427, 256kbps=3437, 2Mbps=26855, 512kbps=6875
- txPackets médio por execução ........ AODV=50593, DSDV=50593, OLSR=49502

**Nenhum problema de consistência encontrado.**

## Síntese

- **PDR (%)** — melhor protocolo por velocidade: 1 m/s: AODV (93.51); 5 m/s: AODV (93.40); 10 m/s: AODV (85.96); 20 m/s: AODV (85.37)
- **Razão de entrega (%)** — melhor protocolo por velocidade: 1 m/s: AODV (93.51); 5 m/s: AODV (93.40); 10 m/s: AODV (85.96); 20 m/s: AODV (85.37)
- **Throughput (Mbps)** — melhor protocolo por velocidade: 1 m/s: AODV (0.98); 5 m/s: AODV (0.98); 10 m/s: AODV (0.90); 20 m/s: AODV (0.90)
- **Atraso médio (ms)** — melhor protocolo por velocidade: 1 m/s: DSDV (11.02); 5 m/s: DSDV (10.49); 10 m/s: DSDV (10.00); 20 m/s: DSDV (11.10)
- **Jitter médio (ms)** — melhor protocolo por velocidade: 1 m/s: DSDV (5.39); 5 m/s: DSDV (5.15); 10 m/s: DSDV (4.88); 20 m/s: DSDV (5.03)

- Kruskal–Wallis: 11 de 20 combinações (velocidade × métrica) com diferença significativa (p < 0,05).
  - PDR @ 5 m/s: H=6.66, p=0.0358 — AODV≠DSDV (p=0.041)
  - Razão de entrega @ 5 m/s: H=6.62, p=0.0366 — AODV≠DSDV (p=0.041)
  - Throughput @ 5 m/s: H=6.62, p=0.0366 — AODV≠DSDV (p=0.041)
  - PDR @ 10 m/s: H=7.33, p=0.0256 — AODV≠DSDV (p=0.026)
  - Razão de entrega @ 10 m/s: H=7.33, p=0.0256 — AODV≠DSDV (p=0.026)
  - Throughput @ 10 m/s: H=7.33, p=0.0256 — AODV≠DSDV (p=0.026)
  - PDR @ 20 m/s: H=17.84, p=0.0001 — AODV≠DSDV (p=0.000), AODV≠OLSR (p=0.002)
  - Razão de entrega @ 20 m/s: H=17.84, p=0.0001 — AODV≠DSDV (p=0.000), AODV≠OLSR (p=0.002)
  - Throughput @ 20 m/s: H=17.84, p=0.0001 — AODV≠DSDV (p=0.000), AODV≠OLSR (p=0.002)
  - Atraso médio @ 20 m/s: H=7.84, p=0.0199 — AODV≠DSDV (p=0.025)
  - Jitter médio @ 20 m/s: H=13.43, p=0.0012 — AODV≠DSDV (p=0.002), DSDV≠OLSR (p=0.008)

- **PDR (%)** — melhor protocolo por taxa: 256kbps: AODV (85.96); 512kbps: OLSR (85.10); 1Mbps: OLSR (80.96); 2Mbps: DSDV (55.56)
- **Razão de entrega (%)** — melhor protocolo por taxa: 256kbps: AODV (85.96); 512kbps: OLSR (85.02); 1Mbps: OLSR (80.02); 2Mbps: DSDV (55.56)
- **Throughput (Mbps)** — melhor protocolo por taxa: 256kbps: AODV (0.90); 512kbps: OLSR (1.79); 1Mbps: OLSR (3.29); 2Mbps: DSDV (4.57)
- **Atraso médio (ms)** — melhor protocolo por taxa: 256kbps: DSDV (10.00); 512kbps: DSDV (13.47); 1Mbps: DSDV (56.56); 2Mbps: DSDV (367.60)
- **Jitter médio (ms)** — melhor protocolo por taxa: 256kbps: DSDV (4.88); 512kbps: DSDV (4.77); 1Mbps: DSDV (4.47); 2Mbps: DSDV (3.16)

- Kruskal–Wallis (taxa): 15 de 20 combinações com diferença significativa (p < 0,05).

### Efeito do fator dentro de cada protocolo (Kruskal–Wallis)

Testa se a velocidade (experimento `base`) ou a taxa (`rate`) altera a métrica **dentro** de cada protocolo — pergunta distinta de "os protocolos diferem entre si em um dado nível do fator?".

- [base] AODV — PDR: H=18.58, p=0.0003 (significativo)
- [base] AODV — Razão de entrega: H=18.58, p=0.0003 (significativo)
- [base] AODV — Throughput: H=18.58, p=0.0003 (significativo)
- [base] AODV — Atraso médio: H=3.34, p=0.3421 (não significativo)
- [base] AODV — Jitter médio: H=1.27, p=0.7356 (não significativo)
- [base] DSDV — PDR: H=45.09, p=0.0000 (significativo)
- [base] DSDV — Razão de entrega: H=45.09, p=0.0000 (significativo)
- [base] DSDV — Throughput: H=45.09, p=0.0000 (significativo)
- [base] DSDV — Atraso médio: H=3.77, p=0.2868 (não significativo)
- [base] DSDV — Jitter médio: H=1.30, p=0.7284 (não significativo)
- [base] OLSR — PDR: H=41.93, p=0.0000 (significativo)
- [base] OLSR — Razão de entrega: H=41.84, p=0.0000 (significativo)
- [base] OLSR — Throughput: H=41.84, p=0.0000 (significativo)
- [base] OLSR — Atraso médio: H=7.90, p=0.0481 (significativo)
- [base] OLSR — Jitter médio: H=4.18, p=0.2424 (não significativo)
- [rate] AODV — PDR: H=74.50, p=0.0000 (significativo)
- [rate] AODV — Razão de entrega: H=74.50, p=0.0000 (significativo)
- [rate] AODV — Throughput: H=98.00, p=0.0000 (significativo)
- [rate] AODV — Atraso médio: H=104.66, p=0.0000 (significativo)
- [rate] AODV — Jitter médio: H=62.52, p=0.0000 (significativo)
- [rate] DSDV — PDR: H=37.78, p=0.0000 (significativo)
- [rate] DSDV — Razão de entrega: H=37.78, p=0.0000 (significativo)
- [rate] DSDV — Throughput: H=106.99, p=0.0000 (significativo)
- [rate] DSDV — Atraso médio: H=96.70, p=0.0000 (significativo)
- [rate] DSDV — Jitter médio: H=40.17, p=0.0000 (significativo)
- [rate] OLSR — PDR: H=63.57, p=0.0000 (significativo)
- [rate] OLSR — Razão de entrega: H=64.38, p=0.0000 (significativo)
- [rate] OLSR — Throughput: H=107.00, p=0.0000 (significativo)
- [rate] OLSR — Atraso médio: H=99.75, p=0.0000 (significativo)
- [rate] OLSR — Jitter médio: H=9.92, p=0.0193 (significativo)
