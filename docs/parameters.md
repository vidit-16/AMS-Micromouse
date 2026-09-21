# Simulator parameters

The simulator takes `key=value` arguments. Unknown keys are rejected with an error.

```bash
./build/micromouse_sim b0=0.85 rhoP=0.15 reps=10
```

## Run control

| Key | Default | Meaning |
|---|---|---|
| `mode` | `run` | `run` prints one CSV row per trial; `trace` prints the walls, exploration path and speed-run path of a single maze |
| `nmazes` | `100` | Number of mazes (maze *i* is generated from seed *i*) |
| `reps` | `10` | Repetitions per maze (each with its own noise seed, shared across strategies) |
| `maze` | `0` | Maze index used in `trace` mode |
| `braid` | `0.10` | Fraction of remaining interior walls removed after generation (adds loops). The experiment scripts use `0.05` |

The maze is fixed at 16 × 16 cells with the start in the top-left corner (open to the east) and an open 2 × 2 goal in the centre.

## Degradation model

The true slowdown of primitive *m* at elapsed motion time *T* is `(1 / b(T)) · (1 + ρ_m)`.

| Key | Default | Meaning |
|---|---|---|
| `b0` | `1.0` | Initial speed factor (battery voltage); `b(T) = max(0.3, b0 − kappa · T[s])` |
| `kappa` | `0.0` | Discharge rate per second of motion |
| `rhoF` | `0.0` | Residual slowdown of forward moves (friction, heating), invisible to a voltage sensor |
| `rhoP` | `0.0` | Residual slowdown of pivots (R, L, U) |
| `sigma` | `0.01` | Relative execution noise per primitive (Gaussian, clipped at −50 %) |

## Exploration model

| Key | Default | Meaning |
|---|---|---|
| `chi` | `1.0` | Transfer factor: fraction of the speed-run slowdown visible at exploration speed |
| `outlier` | `0.0` | Probability that an exploration sample is an outlier (inflated by 1.5–3×) |

## Planner / controller

| Key | Default | Meaning |
|---|---|---|
| `margin` | `0.02` | Command margin μ added to every commanded primitive time |
| `safe` | `0.35` | Margin used by the Fixed-Safe baseline |
| `tau` | `0.0` | AMS drift threshold (%): AMS switches to the learned model only if max drift exceeds it |
| `vgain` | `1.0` | Voltage-sensor gain error (VC, Hybrid) |
| `vnoise` | `0.0` | Voltage-sensor relative noise (VC, Hybrid) |

A trial **fails** when a commanded primitive time is below 98 % of the time the robot actually needs.

## Primitive timings (compiled in)

| Primitive | Speed run (ms) | Exploration (ms) |
|---|---|---|
| F (one 180 mm cell) | 100 | 300 |
| R / L (90° pivot) | 180 | 360 |
| U (180° pivot) | 300 | 540 |

## Output columns (`mode=run`)

`maze, rep, strategy, success, time_ms, steps, fail_step, explore_ms, switched, replanned, replan_gain, ff_gain, max_drift, b_run, est_F, est_U, est_R, est_L, n_F, n_U, n_R, n_L`

- `replan_gain`: % time saved by the chosen path over the path the fixed cost table would pick (both costed with the strategy's table).
- `ff_gain`: % saved over a cell-count shortest path (flood-fill style).
- `est_*`, `n_*`: learned per-primitive factors and sample counts (AMS / Hybrid only).

The experiment scripts add the parameter columns and an `exp` (experiment id) and `scen` (E1 scenario) column.
