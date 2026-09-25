# Experiments

All experiments run 8 strategies on braided mazes (`braid=0.05`, `sigma=0.01`, `margin=0.02` unless varied). Results are stored together in `results/all_runs.csv.gz`; the `exp` column identifies the experiment.

| Id | Script | Varies | Fixed settings | Reps |
|---|---|---|---|---|
| **E1** | `run_experiments.py` | Scenario S0–S3 | — | 10 |
| **E2** | `run_experiments.py` | `b0` 0.70 → 1.00 | — | 5 |
| **E3** | `run_experiments.py` | `rhoP` 0 → 30 % | — | 5 |
| **E4** | `run_experiments.py` | `tau` ∈ {0, 0.5, 1, 2, 3, 5} % × `b0` 0.95 → 1.00 | — | 5 |
| **E5** | `run_experiments.py` | `sigma` 0 → 3 % × `margin` 0 → 6 % | `b0=0.85` | 5 |
| **E6** | `run_experiments.py` | `chi` 0.80 → 1.00 | S3 | 5 |
| **E6b** | `run_sensor_experiments.py` | `chi` 0 → 1.00 | S1 | 5 |
| **E7** | `run_experiments.py` | `outlier` 0 → 20 % | `b0=0.85` | 5 |
| **E7b** | `run_experiments.py` | `outlier` 0 → 20 % | S3 | 5 |
| **E8** | `run_experiments.py` | `kappa` 0 → 3·10⁻⁴ s⁻¹ | `rhoP=0.10` | 5 |
| **E8b** | `run_experiments.py` | `kappa` 0 → 3·10⁻⁴ s⁻¹ | `rhoP=0` | 5 |
| **E9** | `run_experiments.py` | `braid` ∈ {0, 0.05, 0.10} | S3 | 10 |
| **E10** | `run_sensor_experiments.py` | `vgain` 0.94 → 1.08 | S1 | 5 |
| **E10s3** | `run_sensor_experiments.py` | `vgain` 0.94 → 1.08 | S3 | 5 |
| **E10n** | `run_sensor_experiments.py` | `vnoise` 0 → 2 % | S1 | 5 |

## Scenarios (E1)

| Id | Description | `b0` | `rhoF` | `rhoP` |
|---|---|---|---|---|
| S0 | Nominal | 1.00 | 0 | 0 |
| S1 | Voltage sag | 0.85 | 0 | 0 |
| S2 | Friction / heating | 1.00 | 0.03 | 0.15 |
| S3 | Combined | 0.90 | 0.03 | 0.12 |

## Figures

| File | Content |
|---|---|
| `maze_trace` | Maze 0 with exploration coverage and the speed-run path |
| `e1_main` | Success rate and time overhead vs. Oracle per scenario |
| `e23_sweeps` | Success vs. voltage factor and vs. pivot residual |
| `e4_threshold` | Effect of the AMS drift threshold τ |
| `e5_heatmap` | AMS success over execution noise × command margin |
| `e67_transfer_outliers` | Exploration transfer factor and outlier robustness |
| `e8_discharge` | Battery discharge during the run |
| `e10_sensor` | Voltage-sensor gain error and noise |
| `analysis_check` | Closed-form success prediction for Fixed vs. simulation |
