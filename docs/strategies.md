# Planning strategies

Every trial explores the whole maze, returns to the start, builds a cost table for the four motion primitives (F, R, L, U), plans a time-optimal route with Dijkstra over `(x, y, heading)`, and then executes the speed run. Strategies differ only in how they build the cost table and command times.

| Strategy | Cost table / commanded time | Sees voltage? | Learns from exploration? |
|---|---|---|---|
| **Fixed** | Nominal table + margin μ | No | No |
| **Fixed-Safe** | Nominal table + 35 % margin | No | No |
| **VC** | Nominal / measured *b* (voltage feed-forward) | Yes | No |
| **AMS** | Nominal × mean of observed exploration ratios per primitive; used only if drift > τ | No | Yes (mean) |
| **AMS-Med** | As AMS with the median | No | Yes (median) |
| **Hybrid** | Voltage feed-forward × learned voltage-normalised residual (≥ 1) | Yes | Yes (mean) |
| **Hybrid-Med** | As Hybrid with the median | Yes | Yes (median) |
| **Oracle** | True factor at command time (reference only) | — | — |

All strategies use common random numbers: for a given maze and repetition they see the same noise sequence, so differences come from the strategy alone.

## Why it matters

- **Voltage sag** slows every primitive by the same factor. VC handles it, Fixed does not.
- **Friction / heating** slows primitives unevenly (pivots more than straights). A voltage sensor cannot see it, but exploration timings can.
- Once costs change, the time-optimal route can change too (fewer turns vs. fewer cells). `replan_gain` measures this.
