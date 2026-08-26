import pandas as pd, os
from concurrent.futures import ThreadPoolExecutor
from sim_runner import job, RESULTS
J=[]
SC={"S0":dict(b0=1.0),"S1":dict(b0=0.85),"S2":dict(b0=1.0,rhoF=0.03,rhoP=0.15),"S3":dict(b0=0.9,rhoF=0.03,rhoP=0.12)}
for s,kw in SC.items(): J.append(("E1",{**kw,"reps":10,"scen":None} if False else {**kw,"reps":10}))
for i in range(16): J.append(("E2",dict(b0=round(0.70+0.02*i,2),reps=5)))
for i in range(13): J.append(("E3",dict(rhoP=round(0.025*i,3),reps=5)))
for tau in (0,0.5,1,2,3,5):
    for i in range(6): J.append(("E4",dict(tau=tau,b0=round(0.95+0.01*i,2),reps=5)))
for sg in (0,0.005,0.01,0.015,0.02,0.025,0.03):
    for mu in (0,0.01,0.02,0.03,0.04,0.05,0.06): J.append(("E5",dict(b0=0.85,sigma=sg,margin=mu,reps=5)))
for chi in (0.80,0.85,0.90,0.925,0.95,0.975,1.0): J.append(("E6",dict(**SC["S3"],chi=chi,reps=5)))
for q in (0,0.01,0.02,0.05,0.10,0.20): J.append(("E7b",dict(**SC["S3"],outlier=q,reps=5)))
for k in (0,0.5e-4,1e-4,1.5e-4,2e-4,3e-4): J.append(("E8b",dict(b0=1.0,rhoP=0.0,kappa=k,reps=5)))
for q in (0,0.01,0.02,0.05,0.10,0.20): J.append(("E7",dict(b0=0.85,outlier=q,reps=5)))
for k in (0,0.5e-4,1e-4,1.5e-4,2e-4,3e-4): J.append(("E8",dict(b0=1.0,rhoP=0.10,kappa=k,reps=5)))
for br in (0,0.05,0.10): J.append(("E9",dict(**SC["S3"],braid=br,reps=10)))
with ThreadPoolExecutor(os.cpu_count()) as ex: R=list(ex.map(job,J))
d=pd.concat(R,ignore_index=True)
# scenario label for E1
lab={(1.0,0,0):"S0",(0.85,0,0):"S1",(1.0,0.03,0.15):"S2",(0.9,0.03,0.12):"S3"}
d["scen"]=[lab.get((b,f,p),"") if e=="E1" else "" for e,b,f,p in zip(d.exp,d.b0,d.rhoF,d.rhoP)]
RESULTS.mkdir(exist_ok=True); d.to_csv(RESULTS/"all_runs.csv.gz",index=False,compression="gzip")
print(len(d), d.exp.value_counts().sort_index().to_dict())
