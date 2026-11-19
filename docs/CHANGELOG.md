# Changelog

## v3.1

- **VC-Margin baseline**: voltage compensation with a fixed friction allowance (`vcmF` = 5 % on straights, `vcmP` = 20 % on pivots).
- **Fixed-Safe margin** reduced from 35 % to 30 %, the smallest multiple of 5 % that covers the largest slowdown in E1 plus noise.
- **Experiment E11**: voltage-sensor gain error combined with partial exploration transfer in S1.
- Default `braid` is now 0.05, the value used in every experiment.
- `vgain` and `vnoise` are written for every row of `results/all_runs.csv.gz` (they were blank for some experiments).
- Results regenerated: 106,500 trials, 958,500 runs. Rows of E1 to E10 are unchanged.

## v3

Changes from v2, made in response to review feedback:

- **Braided mazes** (`braid` = fraction of interior walls removed) and an open 2 × 2 goal, so routes differ between cost models.
- **Realistic timings**: speed run F / R,L / U = 100 / 180 / 300 ms (1.8 m/s on 180 mm cells); exploration 300 / 360 / 540 ms (0.6 m/s).
- **Non-uniform degradation**: speed factor *b* (voltage) × per-primitive residual (1 + ρ) for friction / heating.
- **Exploration transfer factor** χ and outlier samples (rate *q*).
- The robot **returns to the start cell** after exploration. The speed run starts there, and the planner may execute U-turns.
- **New baselines**: Fixed-Safe (35 % margin), VC (ideal voltage feed-forward), AMS-Med (median), Hybrid and Hybrid-Med (voltage feed-forward × learned residual), Oracle.
- **Voltage-sensor model** for VC / Hybrid: gain error (`vgain`) and relative noise (`vnoise`).
- **Extra metrics**: route change vs. the fixed table (`replanned`, `replan_gain`) and gain of the turn-aware planner over a cell-count shortest path (`ff_gain`).
