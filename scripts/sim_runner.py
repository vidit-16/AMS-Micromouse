import subprocess, pandas as pd, io, os, sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parent.parent
RESULTS=ROOT/"results"
SIM=os.environ.get("SIM_BIN") or str(ROOT/"build"/("micromouse_sim.exe" if sys.platform=="win32" else "micromouse_sim"))
BASE=dict(braid=0.05,sigma=0.01,margin=0.02,tau=0,chi=1,outlier=0,kappa=0,b0=1.0,rhoF=0,rhoP=0)
def job(a):
    tag,kw=a; p={**BASE,**kw}
    args=[SIM]+[f"{k}={v}" for k,v in p.items()]
    out=subprocess.run(args,capture_output=True,text=True,check=True).stdout
    d=pd.read_csv(io.StringIO(out)); d["exp"]=tag
    for k,v in p.items(): d[k]=v
    return d
