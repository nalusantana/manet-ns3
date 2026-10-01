# Relatório de análise — MANET + ns-3

Gerado por `scripts/analyze.py` a partir dos CSVs brutos em `data/raw/`.

## Experimento: base (variável = velocidade (m/s))

### Validação — base

- Linhas brutas (fluxos) .............. 1438
- Execuções agregadas ................. 360
- Protocolos .......................... ['AODV', 'DSDV', 'OLSR']
- Valores da variável (speed) ..... [np.float64(1.0), np.float64(5.0), np.float64(10.0), np.float64(20.0)]
- Runs por célula ..................... [np.int64(1), np.int64(2), np.int64(3), np.int64(4), np.int64(5), np.int64(6), np.int64(7), np.int64(8), np.int64(9), np.int64(10), np.int64(11), np.int64(12), np.int64(13), np.int64(14), np.int64(15), np.int64(16), np.int64(17), np.int64(18), np.int64(19), np.int64(20), np.int64(21), np.int64(22), np.int64(23), np.int64(24), np.int64(25), np.int64(26), np.int64(27), np.int64(28), np.int64(29), np.int64(30)]
- Fluxos por execução ................. min=3 max=4 (esperado 4)
- 30 runs em todas as células .......... OK
- Execuções esperadas ................. 360 / obtidas 360
- Fluxos sem recepção (rx=0) .......... 6 (excluídos de atraso/jitter)
- Execuções com ≥1 fluxo sem recepção . 6
- Pacotes oferecidos por fluxo ........ 256kbps=3437
- txPackets médio por execução ........ AODV=13748, DSDV=13748, OLSR=10689

**Problemas encontrados:**
- 2 execuções com menos fluxos observados que o configurado (total oferecido reconstruído): OLSR/1.0/run15=3, OLSR/1.0/run21=3

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
- Fluxos sem recepção (rx=0) .......... 0 (excluídos de atraso/jitter)
- Execuções com ≥1 fluxo sem recepção . 0
- Pacotes oferecidos por fluxo ........ 1Mbps=13427, 256kbps=3437, 2Mbps=26855, 512kbps=6875
- txPackets médio por execução ........ AODV=50593, DSDV=50593, OLSR=34655

**Nenhum problema de consistência encontrado.**

## Síntese

- **PDR (%)** — melhor protocolo por velocidade: 1 m/s: OLSR (83.30); 5 m/s: OLSR (64.24); 10 m/s: AODV (51.23); 20 m/s: AODV (41.41)
- **Razão de entrega (%)** — melhor protocolo por velocidade: 1 m/s: OLSR (66.10); 5 m/s: AODV (56.46); 10 m/s: AODV (51.23); 20 m/s: AODV (41.41)
- **Throughput (Mbps)** — melhor protocolo por velocidade: 1 m/s: OLSR (0.70); 5 m/s: AODV (0.59); 10 m/s: AODV (0.54); 20 m/s: AODV (0.44)
- **Atraso médio (ms)** — melhor protocolo por velocidade: 1 m/s: OLSR (52.59); 5 m/s: OLSR (36.92); 10 m/s: OLSR (32.59); 20 m/s: OLSR (23.38)
- **Jitter médio (ms)** — melhor protocolo por velocidade: 1 m/s: OLSR (13.96); 5 m/s: OLSR (13.29); 10 m/s: OLSR (11.01); 20 m/s: OLSR (9.33)

- Kruskal–Wallis: 16 de 20 combinações (velocidade × métrica) com diferença significativa (p < 0,05).
  - PDR @ 1 m/s: H=28.46, p=0.0000 — AODV≠OLSR (p=0.000), DSDV≠OLSR (p=0.000)
  - PDR @ 5 m/s: H=24.38, p=0.0000 — AODV≠DSDV (p=0.016), AODV≠OLSR (p=0.016), DSDV≠OLSR (p=0.000)
  - Razão de entrega @ 5 m/s: H=7.80, p=0.0202 — AODV≠DSDV (p=0.024)
  - Throughput @ 5 m/s: H=7.80, p=0.0202 — AODV≠DSDV (p=0.024)
  - Atraso médio @ 5 m/s: H=10.77, p=0.0046 — AODV≠OLSR (p=0.003)
  - Jitter médio @ 5 m/s: H=11.60, p=0.0030 — AODV≠OLSR (p=0.002)
  - PDR @ 10 m/s: H=29.24, p=0.0000 — AODV≠DSDV (p=0.000), DSDV≠OLSR (p=0.000)
  - Razão de entrega @ 10 m/s: H=30.26, p=0.0000 — AODV≠DSDV (p=0.000), AODV≠OLSR (p=0.000)
  - Throughput @ 10 m/s: H=30.26, p=0.0000 — AODV≠DSDV (p=0.000), AODV≠OLSR (p=0.000)
  - Atraso médio @ 10 m/s: H=17.19, p=0.0002 — AODV≠DSDV (p=0.037), AODV≠OLSR (p=0.000)
  - Jitter médio @ 10 m/s: H=22.09, p=0.0000 — AODV≠DSDV (p=0.028), AODV≠OLSR (p=0.000), DSDV≠OLSR (p=0.028)
  - PDR @ 20 m/s: H=41.25, p=0.0000 — AODV≠DSDV (p=0.000), AODV≠OLSR (p=0.000), DSDV≠OLSR (p=0.019)
  - Razão de entrega @ 20 m/s: H=50.95, p=0.0000 — AODV≠DSDV (p=0.000), AODV≠OLSR (p=0.000)
  - Throughput @ 20 m/s: H=50.95, p=0.0000 — AODV≠DSDV (p=0.000), AODV≠OLSR (p=0.000)
  - Atraso médio @ 20 m/s: H=45.86, p=0.0000 — AODV≠DSDV (p=0.000), AODV≠OLSR (p=0.000), DSDV≠OLSR (p=0.003)
  - Jitter médio @ 20 m/s: H=40.29, p=0.0000 — AODV≠DSDV (p=0.000), AODV≠OLSR (p=0.000), DSDV≠OLSR (p=0.013)

- **PDR (%)** — melhor protocolo por taxa: 256kbps: AODV (51.23); 512kbps: OLSR (46.67); 1Mbps: OLSR (40.86); 2Mbps: OLSR (32.10)
- **Razão de entrega (%)** — melhor protocolo por taxa: 256kbps: AODV (51.23); 512kbps: AODV (39.47); 1Mbps: AODV (30.48); 2Mbps: OLSR (20.92)
- **Throughput (Mbps)** — melhor protocolo por taxa: 256kbps: AODV (0.54); 512kbps: AODV (0.83); 1Mbps: AODV (1.25); 2Mbps: OLSR (1.72)
- **Atraso médio (ms)** — melhor protocolo por taxa: 256kbps: OLSR (32.59); 512kbps: OLSR (48.12); 1Mbps: OLSR (116.56); 2Mbps: OLSR (209.55)
- **Jitter médio (ms)** — melhor protocolo por taxa: 256kbps: OLSR (11.01); 512kbps: OLSR (10.00); 1Mbps: OLSR (8.02); 2Mbps: DSDV (5.23)

- Kruskal–Wallis (taxa): 16 de 20 combinações com diferença significativa (p < 0,05).

### Efeito do fator dentro de cada protocolo (Kruskal–Wallis)

Testa se a velocidade (experimento `base`) ou a taxa (`rate`) altera a métrica **dentro** de cada protocolo — pergunta distinta de "os protocolos diferem entre si em um dado nível do fator?".

- [base] AODV — PDR: H=35.72, p=0.0000 (significativo)
- [base] AODV — Razão de entrega: H=35.72, p=0.0000 (significativo)
- [base] AODV — Throughput: H=35.72, p=0.0000 (significativo)
- [base] AODV — Atraso médio: H=3.09, p=0.3785 (não significativo)
- [base] AODV — Jitter médio: H=0.55, p=0.9070 (não significativo)
- [base] DSDV — PDR: H=66.64, p=0.0000 (significativo)
- [base] DSDV — Razão de entrega: H=66.64, p=0.0000 (significativo)
- [base] DSDV — Throughput: H=66.64, p=0.0000 (significativo)
- [base] DSDV — Atraso médio: H=9.28, p=0.0258 (significativo)
- [base] DSDV — Jitter médio: H=16.32, p=0.0010 (significativo)
- [base] OLSR — PDR: H=92.78, p=0.0000 (significativo)
- [base] OLSR — Razão de entrega: H=83.60, p=0.0000 (significativo)
- [base] OLSR — Throughput: H=83.60, p=0.0000 (significativo)
- [base] OLSR — Atraso médio: H=12.17, p=0.0068 (significativo)
- [base] OLSR — Jitter médio: H=13.01, p=0.0046 (significativo)
- [rate] AODV — PDR: H=74.14, p=0.0000 (significativo)
- [rate] AODV — Razão de entrega: H=74.14, p=0.0000 (significativo)
- [rate] AODV — Throughput: H=85.52, p=0.0000 (significativo)
- [rate] AODV — Atraso médio: H=94.26, p=0.0000 (significativo)
- [rate] AODV — Jitter médio: H=33.92, p=0.0000 (significativo)
- [rate] DSDV — PDR: H=46.16, p=0.0000 (significativo)
- [rate] DSDV — Razão de entrega: H=46.16, p=0.0000 (significativo)
- [rate] DSDV — Throughput: H=83.25, p=0.0000 (significativo)
- [rate] DSDV — Atraso médio: H=93.79, p=0.0000 (significativo)
- [rate] DSDV — Jitter médio: H=72.26, p=0.0000 (significativo)
- [rate] OLSR — PDR: H=31.32, p=0.0000 (significativo)
- [rate] OLSR — Razão de entrega: H=41.49, p=0.0000 (significativo)
- [rate] OLSR — Throughput: H=94.20, p=0.0000 (significativo)
- [rate] OLSR — Atraso médio: H=96.80, p=0.0000 (significativo)
- [rate] OLSR — Jitter médio: H=41.78, p=0.0000 (significativo)
