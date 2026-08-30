import pandas as pd, os
from concurrent.futures import ThreadPoolExecutor
from sim_runner import job, RESULTS
S1=dict(b0=0.85); S3=dict(b0=0.9,rhoF=0.03,rhoP=0.12)
J=[]
for g in (0.94,0.96,0.98,0.99,1.0,1.01,1.02,1.03,1.04,1.06,1.08):
    J.append(("E10",dict(**S1,vgain=g,reps=5))); J.append(("E10s3",dict(**S3,vgain=g,reps=5)))
for vn in (0,0.0025,0.005,0.01,0.015,0.02): J.append(("E10n",dict(**S1,vnoise=vn,reps=5)))
for chi in (0.0,0.25,0.5,0.75,0.9,1.0): J.append(("E6b",dict(**S1,chi=chi,reps=5)))
with ThreadPoolExecutor(os.cpu_count()) as ex: R=list(ex.map(job,J))
n=pd.concat(R,ignore_index=True); n["scen"]=""
a=pd.read_csv(RESULTS/"all_runs.csv.gz",low_memory=False)
a=a[~a.exp.isin(["E10","E10s3","E10n","E6b"])]
if "vgain" not in a: a["vgain"]=1.0
if "vnoise" not in a: a["vnoise"]=0.0
d=pd.concat([a,n],ignore_index=True); d.to_csv(RESULTS/"all_runs.csv.gz",index=False,compression="gzip")
O=["Fixed","Fixed-Safe","VC","AMS","AMS-Med","Hybrid","Hybrid-Med","Oracle"]
for e,idx in [("E10","vgain"),("E10s3","vgain"),("E10n","vnoise"),("E6b","chi")]:
    print("==",e); print((d[d.exp==e].pivot_table(index=idx,columns="strategy",values="success")*100).round(1)[O].to_string())
    rows={}
    for v,g in d[d.exp==e].groupby(idx):
        p=g.pivot_table(index=["maze","rep"],columns="strategy",values="time_ms")
        rows[v]={s:round(100*((p[s][(p[s]>0)&(p.Oracle>0)]/p.Oracle[(p[s]>0)&(p.Oracle>0)])-1).mean(),2) if ((p[s]>0)&(p.Oracle>0)).sum() else None for s in ["VC","AMS","Hybrid-Med"]}
    print(pd.DataFrame(rows).T)
print(len(d))
