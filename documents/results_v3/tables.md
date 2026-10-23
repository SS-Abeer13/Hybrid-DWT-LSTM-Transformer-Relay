# Results tables (generated from saved files by lstm_models/make_tables_v3.py)

## Table 1 - Ablation and main result (grouped 5-fold CV, 3 repetitions, 3,218 traces each tested once per repetition)

Mean (sd across the 3 repetitions) of the pooled out-of-fold decisions. Undetectable faults (< 0.05 pu, 94 traces) excluded.

| variant | dependability % | security % | operate median ms | within 2 cycles % | pre-fault trips |
|---|---|---|---|---|---|
| 87T alone | 79.62 (0.00) | 52.96 (0.00) | 0.6 | 100.0 | 124.0 |
| LSTM alone | 99.31 (0.28) | 99.56 (0.22) | 15.4 | 97.1 | 0.0 |
| Hybrid (87T gate) | 89.40 (0.05) | 99.79 (0.14) | 15.2 | 97.3 | 0.0 |
| Hybrid + AI-alone path | 99.01 (0.48) | 99.66 (0.24) | 15.6 | 96.9 | 0.0 |

## Table 2 - Per scenario category (hybrid + AI-alone path)

Correct = trip after the measured onset (faults) or no trip (healthy). 95 % Wilson interval from repetition 1; mean and worst repetition over the 3 repetitions; LSTM-alone and 87T-alone means for comparison.

| category | n | expected | correct % [95 % CI] (rep. 1) | mean 3 rep. | worst rep. | LSTM alone mean | 87T alone mean |
|---|---|---|---|---|---|---|---|
| Evolving | 80 | trip | 100.0 [95.4, 100.0] | 100.0 | 100.0 | 100.0 | 100.0 |
| External CT-sat | 241 | no trip | 98.8 [96.4, 99.6] | 99.2 | 98.8 | 98.5 | 34.4 |
| External HiZ | 60 | no trip | 100.0 [94.0, 100.0] | 100.0 | 100.0 | 100.0 | 100.0 |
| External in inrush | 100 | no trip | 99.0 [94.6, 99.8] | 98.7 | 98.0 | 98.7 | 0.0 |
| External solid | 440 | no trip | 99.8 [98.7, 100.0] | 99.9 | 99.8 | 99.8 | 100.0 |
| Fault in inrush | 113 | trip | 100.0 [96.7, 100.0] | 100.0 | 100.0 | 100.0 | 0.0 |
| Inrush loaded | 240 | no trip | 100.0 [98.4, 100.0] | 99.9 | 99.6 | 99.9 | 0.0 |
| Inrush no-load | 200 | no trip | 99.5 [97.2, 99.9] | 99.8 | 99.5 | 99.8 | 0.0 |
| Internal CT-sat | 121 | trip | 100.0 [96.9, 100.0] | 100.0 | 100.0 | 100.0 | 90.9 |
| Internal HV-side | 198 | trip | 100.0 [98.1, 100.0] | 100.0 | 100.0 | 100.0 | 100.0 |
| Internal HiZ | 153 | trip | 89.5 [83.7, 93.5] | 93.0 | 89.5 | 95.2 | 52.3 |
| Internal LV solid | 506 | trip | 100.0 [99.2, 100.0] | 100.0 | 100.0 | 100.0 | 88.5 |
| Normal | 302 | no trip | 100.0 [98.7, 100.0] | 100.0 | 100.0 | 100.0 | 100.0 |
| Over-excitation | 210 | no trip | 100.0 [98.2, 100.0] | 100.0 | 100.0 | 100.0 | 41.9 |
| Recovery inrush | 80 | no trip | 93.8 [86.2, 97.3] | 97.5 | 93.8 | 97.5 | 23.8 |
| SOTF | 80 | trip | 97.5 [91.3, 99.3] | 97.9 | 97.5 | 98.3 | 100.0 |

## Table 3 - Effect of retraining on the realistic v3 data (C1 vs C2)

The deployed model was trained on the light-load v2 data and is scored on all 3,218 v3 traces without retraining (so it has seen none of the new stress cases); the retrained numbers are out-of-fold.

| model / variant | dependability % | security % | missed | false trips |
|---|---|---|---|---|
| deployed v2-trained model, 87T alone | 79.6 | 53.0 | 131 | 881 |
| deployed v2-trained model, Hybrid (87T gate) | 88.0 | 84.8 | 131 | 284 |
| deployed v2-trained model, Hybrid + AI-alone path | 97.1 | 84.1 | 17 | 298 |
| retrained, hybrid + AI-alone (CV mean) | 99.0 | 99.7 | 12 | 6 |

| category | deployed model % | retrained (CV mean) % |
|---|---|---|
| Evolving | 100.0 | 100.0 |
| External CT-sat | 60.2 | 99.2 |
| External HiZ | 100.0 | 100.0 |
| External in inrush | 87.0 | 98.7 |
| External solid | 99.3 | 99.9 |
| Fault in inrush | 84.1 | 100.0 |
| Inrush loaded | 86.7 | 99.9 |
| Inrush no-load | 98.5 | 99.8 |
| Internal CT-sat | 99.2 | 100.0 |
| Internal HV-side | 100.0 | 100.0 |
| Internal HiZ | 89.5 | 93.0 |
| Internal LV solid | 99.8 | 100.0 |
| Normal | 100.0 | 100.0 |
| Over-excitation | 41.4 | 100.0 |
| Recovery inrush | 65.0 | 97.5 |
| SOTF | 100.0 | 97.9 |

## Table 4 - Out-of-distribution set (300 traces, scored once, final model)

| variant | dependability % | security % | missed | false trips |
|---|---|---|---|---|
| 87T alone | 79.2 | 43.5 | 5 | 83 |
| LSTM alone | 95.1 | 100.0 | 7 | 0 |
| Hybrid (87T gate) | 89.6 | 100.0 | 14 | 0 |
| Hybrid + AI-alone path | 92.4 | 100.0 | 10 | 0 |

| block | content | faults | dependability % | healthy | security % |
|---|---|---|---|---|---|
| 1 | extreme load (1-10 %, 110-130 %) | 30 | 96.7 | 30 | 100.0 |
| 2 | weak source 3x + 49.5/50.5 Hz | 30 | 100.0 | 30 | 100.0 |
| 3 | CT burden 12-16x | 25 | 68.0 | 27 | 100.0 |
| 4 | over-excitation 1.5-1.6 pu + flux 0.9 pu | 30 | 93.3 | 30 | 100.0 |
| 5 | noise 5 % + CT mismatch +/-8 % | 29 | 100.0 | 30 | 100.0 |

## Table 5 - Extended closed-loop benchmark (Simulink, LSTM active, 12 cases)

| case | expected | actual | LSTM max prob | trip delay ms | status |
|---|---|---|---|---|---|
| Normal, 30 % load | BLOCK | BLOCK | 0.0004 | - | PASS |
| Normal, 100 % load | BLOCK | BLOCK | 0.0001 | - | PASS |
| Inrush 0.8 pu remanence, 0 deg | BLOCK | BLOCK | 0.0673 | - | PASS |
| Recovery inrush (HV bus, 50 ms) | BLOCK | BLOCK | 0.0306 | - | PASS |
| Over-excitation 1.3 pu | BLOCK | BLOCK | 0.0000 | - | PASS |
| External 3-phase solid | BLOCK | BLOCK | 0.0000 | - | PASS |
| External A-G + CT saturation 8 x | BLOCK | BLOCK | 0.0002 | - | PASS |
| Internal A-G solid (LV side) | TRIP | TRIP | 1.0000 | 15.0 | PASS |
| Internal A-B, HV side | TRIP | TRIP | 1.0000 | 0.6 | PASS |
| Internal HiZ A-B, AI-only bin | TRIP | TRIP | 1.0000 | 47.5 | FAIL |
| SOTF A-B | TRIP | TRIP | 1.0000 | 13.8 | PASS |
| Fault during inrush A-B-G | TRIP | TRIP | 1.0000 | 41.3 | FAIL |

## Table 6 - Closed-loop vs Python mirror (D4)

```
Decision agreement: 50 / 50 = 100.0 %  (criterion >= 98 %)
Trip-time difference Simulink - mirror over 21 common trips: median 0.00 ms, mean 0.82, p95 8.45, max |dt| 8.85 ms  (criterion median <= 2 ms)
Simulink correct vs ground truth: 50 / 50; mirror correct: 50 / 50
```

Per-trace comparison:

```
Simulink closed loop (LSTM active, saved model) vs Python relay mirror (final model, AI 0.99, solo 0.998, dwell 20) on 50 traces: 25 held-out validation traces of the final model + 25 OOD traces

set       # scenario                   mirror  simulink   dt ms
main    137 Normal                     block   block          -
main    183 Normal                     block   block          -
main    198 Normal                     block   block          -
main    322 Inrush_NoLoad              block   block          -
main    655 Recovery_Inrush            block   block          -
main    728 Overexcitation             block   block          -
main    830 Overexcitation             block   block          -
main    888 Internal_Evolving          TRIP    TRIP         0.0
main   1092 Stress_FaultInInrush       TRIP    TRIP         0.0
main   1227 Stress_ExtInInrush         block   block          -
main   1316 Internal_AG                TRIP    TRIP         0.0
main   1594 Internal_CG                TRIP    TRIP         0.0
main   1751 InternalHV_AB              TRIP    TRIP         8.9
main   1783 External_AB                block   block          -
main   1872 Internal_BC                TRIP    TRIP         0.0
main   2056 External_AC                block   block          -
main   2113 Stress_CTSat_Int_AC        TRIP    TRIP         0.0
main   2137 Internal_ABG               TRIP    TRIP         0.0
main   2188 External_ABG               block   block          -
main   2232 Stress_ExtCTSat_ABG        block   block          -
main   2354 External_BCG               block   block          -
main   2421 Internal_ACG               TRIP    TRIP         0.0
main   2463 External_ACG               block   block          -
main   2869 Internal_HiZ_BC            TRIP    TRIP         0.0
main   2989 Internal_HiZ_ABC           TRIP    TRIP         0.0
ood       5 Normal                     block   block          -
ood      23 External_AB                block   block          -
ood      25 Inrush_Loaded              block   block          -
ood      28 Inrush_Loaded              block   block          -
ood      29 Inrush_Loaded              block   block          -
ood      30 Inrush_Loaded              block   block          -
ood      31 Internal_AB                TRIP    TRIP         0.0
ood      32 Internal_AB                TRIP    TRIP         0.0
ood      33 Internal_AB                TRIP    TRIP         0.0
ood      35 Internal_AB                TRIP    TRIP         0.0
ood      58 Internal_AG                TRIP    TRIP         0.0
ood      83 Inrush_Loaded              block   block          -
ood      84 Inrush_Loaded              block   block          -
ood     114 InternalHV_AG              TRIP    TRIP         0.0
ood     133 Stress_ExtCTSat_AB         block   block          -
ood     139 Stress_ExtCTSat_AB         block   block          -
ood     150 Stress_ExtCTSat_AG         block   block          -
ood     195 Inrush_NoLoad              block   block          -
ood     197 Inrush_NoLoad              block   block          -
ood     212 Internal_AB                TRIP    TRIP         0.0
ood     226 Internal_SOTF_AB           TRIP    TRIP         0.0
ood     228 Internal_SOTF_AB           TRIP    TRIP         0.0
ood     242 Normal                     block   block          -
ood     243 Normal                     block   block          -
ood     294 InternalHV_AB              TRIP    TRIP         8.5
```

## Table 7 - Internal HiZ faults by Rf bin (repetition 1)

```
Internal HiZ faults by Rf bin, pooled out-of-fold (20261021_v3_cv5); 'tripped after onset' for every trace, including the undetectable bin

bin                                 n  faultDiffPu median |                87T alone |               LSTM alone |        Hybrid (87T gate) |   Hybrid + AI-alone path
87T-visible (Rf 0.3-1.2 ohm)       80               0.529 |       96.2% [89.5, 98.7] |      100.0% [95.4,100.0] |       96.2% [89.5, 98.7] |      100.0% [95.4,100.0]
AI-only (1.2-7 ohm)                80               0.115 |        3.8% [ 1.3, 10.5] |       80.0% [70.0, 87.3] |        3.8% [ 1.3, 10.5] |       71.2% [60.5, 80.0]
below detect limit (7-21 ohm)      80               0.026 |        0.0% [ 0.0,  4.6] |        1.2% [ 0.2,  6.7] |        0.0% [ 0.0,  4.6] |        0.0% [ 0.0,  4.6]
```
