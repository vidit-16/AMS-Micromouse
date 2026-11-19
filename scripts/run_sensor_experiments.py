"""Experiments E10 (voltage sensor), E6b (transfer in S1) and E11 (gain error x transfer in S1).
Adds its rows to results/all_runs.csv.gz, replacing earlier rows of the same experiments."""
import os
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from sim_runner import RESULTS, SCENARIOS as SC, STRATEGIES, job

S1, S3 = SC["S1"], SC["S3"]
J = []
for g in (0.94, 0.96, 0.98, 0.99, 1.0, 1.01, 1.02, 1.03, 1.04, 1.06, 1.08):
    J.append(("E10", dict(**S1, vgain=g, reps=5)))
    J.append(("E10s3", dict(**S3, vgain=g, reps=5)))
for vn in (0, 0.0025, 0.005, 0.01, 0.015, 0.02):
    J.append(("E10n", dict(**S1, vnoise=vn, reps=5)))
for chi in (0.0, 0.25, 0.5, 0.75, 0.9, 1.0):
    J.append(("E6b", dict(**S1, chi=chi, reps=5)))
for g in (1.0, 1.01, 1.02, 1.04):
    for chi in (0.5, 0.75, 0.9, 0.95, 1.0):
        J.append(("E11", dict(**S1, vgain=g, chi=chi, reps=5)))
MINE = sorted({tag for tag, _ in J})

with ThreadPoolExecutor(os.cpu_count()) as ex:
    R = list(ex.map(job, J))
n = pd.concat(R, ignore_index=True)
n["scen"] = ""
a = pd.read_csv(RESULTS / "all_runs.csv.gz", low_memory=False, keep_default_na=False)
a = a[~a.exp.isin(MINE)]
d = pd.concat([a, n], ignore_index=True)[list(a.columns)]
d.to_csv(RESULTS / "all_runs.csv.gz", index=False, compression="gzip")

for e, idx in [("E10", "vgain"), ("E10s3", "vgain"), ("E10n", "vnoise"), ("E6b", "chi")]:
    print("==", e)
    print((n[n.exp == e].pivot_table(index=idx, columns="strategy", values="success") * 100).round(1)[STRATEGIES].to_string())
print("== E11 Hybrid-Med")
print((n[(n.exp == "E11") & (n.strategy == "Hybrid-Med")].pivot_table(index="chi", columns="vgain", values="success") * 100).round(1).to_string())
print(len(d), d.exp.value_counts().sort_index().to_dict())
