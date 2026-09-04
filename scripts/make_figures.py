import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, numpy as np, pandas as pd, math, os, warnings
from pathlib import Path
from scipy.stats import norm
warnings.filterwarnings("ignore")
plt.rcParams.update({"font.family":"serif","font.size":7.5,"axes.spines.top":False,"axes.spines.right":False,
                     "pdf.fonttype":42,"axes.linewidth":0.6,"xtick.major.width":0.6,"ytick.major.width":0.6,"legend.handlelength":1.5})
ROOT=Path(__file__).resolve().parent.parent
OUT=str(ROOT/"figs"); os.makedirs(OUT,exist_ok=True)
for f in os.listdir(OUT): os.remove(os.path.join(OUT,f))
d=pd.read_csv(ROOT/"results"/"all_runs.csv.gz",low_memory=False)
COL={"Fixed":"#4C72B0","Fixed-Safe":"#8172B2","VC":"#64B5CD","AMS":"#DD8452","AMS-Med":"#C44E52","Hybrid":"#55A868","Hybrid-Med":"#2E7D32","Oracle":"#333333"}
MK={"Fixed":"o","Fixed-Safe":"v","VC":"D","AMS":"s","AMS-Med":"P","Hybrid":"^","Hybrid-Med":"^","Oracle":None}
LS={"Oracle":"--"}
MAIN=["Fixed","Fixed-Safe","VC","AMS","Hybrid-Med","Oracle"]
def wil(k,n,z=1.959964):
    p=k/n; dd=1+z*z/n; c=(p+z*z/(2*n))/dd; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/dd; return c-h,min(1,c+h)
def save(fig,name): fig.tight_layout(pad=0.3); fig.savefig(f"{OUT}/{name}.pdf",bbox_inches="tight",pad_inches=0.02); fig.savefig(f"{OUT}/{name}.png",dpi=200,bbox_inches="tight",pad_inches=0.02); plt.close(fig)
def line(ax,x,y,s,**kw):
    # small horizontal offsets keep overlapping series visible
    off={"Fixed":0,"Fixed-Safe":0,"VC":0,"AMS":0,"AMS-Med":0,"Hybrid":0,"Oracle":0}
    ax.plot(x,y,LS.get(s,"-"),color=COL[s],marker=MK[s],ms=2.6,lw=1.0,label=s,**kw)

# ---- maze trace
L=open(ROOT/"results"/"trace_maze0.txt").read().strip().split("\n")
walls=list(map(int,L[0].split(",")[1:])); ex=[tuple(map(int,c.split(":"))) for c in L[1].split(",")[1:]]
rn=[tuple(map(int,c.split(":"))) for c in L[2].split(",")[1:]]
fig,ax=plt.subplots(figsize=(3.1,3.1)); vis=np.zeros((16,16))
for (x,y) in ex: vis[y,x]+=1
ax.imshow(np.log1p(vis),cmap="Blues",extent=(0,16,16,0),alpha=0.55,vmin=0)
for y in range(16):
    for x in range(16):
        w=walls[y*16+x]
        if w&1: ax.plot([x,x+1],[y,y],"k",lw=1.0)
        if w&2: ax.plot([x+1,x+1],[y,y+1],"k",lw=1.0)
        if w&4: ax.plot([x,x+1],[y+1,y+1],"k",lw=1.0)
        if w&8: ax.plot([x,x],[y,y+1],"k",lw=1.0)
px=[c[0]+0.5 for c in rn]; py=[c[1]+0.5 for c in rn]
ax.plot(px,py,color=COL["AMS"],lw=2.0,solid_capstyle="round",label="Speed-run path")
ax.add_patch(plt.Rectangle((7,7),2,2,fill=False,ec="#C44E52",lw=1.5,ls="--"))
ax.plot(0.5,0.5,marker="o",color="#2b2b2b",ms=4.5); ax.text(0.5,-0.35,"Start",ha="center",fontsize=6.5)
ax.text(8,6.75,"Goal",ha="center",fontsize=6.5,color="#C44E52")
ax.set_xlim(-0.1,16.1); ax.set_ylim(16.1,-0.9); ax.set_aspect("equal"); ax.axis("off")
ax.legend(loc="lower center",bbox_to_anchor=(0.5,-0.08),frameon=False,fontsize=6.5)
save(fig,"maze_trace")

# ---- E1: success (a) and time overhead vs oracle (b)
e1=d[d.exp=="E1"]; SC=["S0","S1","S2","S3"]
fig,axs=plt.subplots(2,1,figsize=(3.45,3.2),gridspec_kw={"height_ratios":[1.15,1]})
w=0.13; x=np.arange(4)
ax=axs[0]
for j,s in enumerate(MAIN):
    v=[100*e1[(e1.scen==c)&(e1.strategy==s)].success.mean() for c in SC]
    ax.bar(x+(j-2.5)*w,v,w,color=COL[s],label=s)
    for xi,vi in zip(x+(j-2.5)*w,v):
        if vi<1: ax.text(xi,2,"0",ha="center",fontsize=5.2,color=COL[s])
ax.set_xticks(x); ax.set_xticklabels(["S0 nominal","S1 voltage","S2 friction","S3 combined"],fontsize=6.6)
ax.set_ylabel("Success (%)"); ax.set_ylim(0,112); ax.set_yticks([0,25,50,75,100]); ax.set_title("(a)",fontsize=7,pad=2)
ax.legend(frameon=False,ncol=6,fontsize=5.7,loc="upper center",bbox_to_anchor=(0.5,1.30),handlelength=1.0,columnspacing=0.6)
ax=axs[1]
for j,s in enumerate(MAIN):
    v=[]
    for c in SC:
        p=e1[e1.scen==c].pivot_table(index=["maze","rep"],columns="strategy",values="time_ms")
        ok=(p[s]>0)&(p.Oracle>0); v.append(100*((p[s][ok]/p.Oracle[ok])-1).mean() if ok.sum() else np.nan)
    vv=[0 if np.isnan(a) else a for a in v]
    ax.bar(x+(j-2.5)*w,vv,w,color=COL[s])
    for xi,a in zip(x+(j-2.5)*w,v):
        if np.isnan(a): ax.text(xi,0.6,"×",ha="center",fontsize=6,color=COL[s])
ax.set_xticks(x); ax.set_xticklabels(["S0","S1","S2","S3"]); ax.set_ylabel("Time vs. Oracle (%)")
ax.set_title("(b)",fontsize=7,pad=2); ax.set_ylim(0,36)
save(fig,"e1_main")

# ---- E2 / E3 sweeps
fig,axs=plt.subplots(1,2,figsize=(3.45,1.85),sharey=True)
e2=d[d.exp=="E2"].pivot_table(index="b0",columns="strategy",values="success")*100
e3=d[d.exp=="E3"].pivot_table(index="rhoP",columns="strategy",values="success")*100
for s in MAIN: line(axs[0],e2.index,e2[s],s); line(axs[1],e3.index*100,e3[s],s)
axs[0].set_xlabel("Speed factor $b_0$"); axs[0].set_ylabel("Success (%)"); axs[0].set_title("(a)",fontsize=7,pad=2)
axs[1].set_xlabel("Pivot residual $\\rho_P$ (%)"); axs[1].set_title("(b)",fontsize=7,pad=2)
axs[0].set_ylim(-4,108)
h,l=axs[0].get_legend_handles_labels(); fig.legend(h,l,frameon=False,ncol=6,fontsize=5.8,loc="upper center",bbox_to_anchor=(0.5,1.07),handlelength=1.3,columnspacing=0.6)
fig.tight_layout(pad=0.3,rect=(0,0,1,0.92)); fig.savefig(f"{OUT}/e23_sweeps.pdf",bbox_inches="tight",pad_inches=0.02); fig.savefig(f"{OUT}/e23_sweeps.png",dpi=200,bbox_inches="tight",pad_inches=0.02); plt.close(fig)

# ---- E4 threshold
e4=d[(d.exp=="E4")&(d.strategy=="AMS")]
fig,axs=plt.subplots(1,2,figsize=(3.45,1.75),sharex=True)
cm=plt.get_cmap("viridis")
for i,tau in enumerate((0,0.5,1,2,3,5)):
    g=e4[e4.tau==tau]; c=cm(i/5)
    axs[0].plot(g.groupby("b0").switched.mean().index,g.groupby("b0").switched.mean()*100,"-o",ms=2,lw=0.9,color=c,label=f"$\\tau$={tau:g}%")
    axs[1].plot(g.groupby("b0").success.mean().index,g.groupby("b0").success.mean()*100,"-o",ms=2,lw=0.9,color=c)
axs[0].set_ylabel("Uses learned model (%)"); axs[1].set_ylabel("Success (%)")
for a,t in zip(axs,["(a)","(b)"]): a.set_xlabel("$b_0$"); a.set_title(t,fontsize=7,pad=2); a.set_xticks([0.95,0.97,0.99])
axs[0].legend(frameon=False,fontsize=5.4,loc="lower left",handlelength=1.0,ncol=1)
save(fig,"e4_threshold")

# ---- E5 heatmap
e5=d[(d.exp=="E5")&(d.strategy=="AMS")]
H=e5.pivot_table(index="sigma",columns="margin",values="success")*100
fig,ax=plt.subplots(figsize=(3.2,2.15))
im=ax.imshow(H.values,cmap="RdYlGn",vmin=0,vmax=100,aspect="auto",origin="lower")
for i in range(H.shape[0]):
    for j in range(H.shape[1]):
        v=H.values[i,j]; ax.text(j,i,f"{v:.0f}",ha="center",va="center",fontsize=5.8,color="w" if v<=20 else "k")
ax.set_xticks(range(H.shape[1])); ax.set_xticklabels([f"{100*m:.0f}" for m in H.columns])
ax.set_yticks(range(H.shape[0])); ax.set_yticklabels([f"{100*s:.1f}" for s in H.index])
ax.set_xlabel("Command margin $\\mu$ (%)"); ax.set_ylabel("Execution noise $\\sigma$ (%)")
cb=fig.colorbar(im,ax=ax,fraction=0.045,pad=0.02); cb.set_label("AMS success (%)",fontsize=6.5); cb.ax.tick_params(labelsize=6)
ax.spines[:].set_visible(False); save(fig,"e5_heatmap")

# ---- E6 transfer + E7 outliers
fig,axs=plt.subplots(1,2,figsize=(3.45,1.8))
e6=d[d.exp=="E6"].pivot_table(index="chi",columns="strategy",values="success")*100
for s in ["VC","AMS","Hybrid-Med","Oracle"]: line(axs[0],e6.index,e6[s],s)
e6b=d[(d.exp=="E6b")&(d.chi>=0.9)].pivot_table(index="chi",columns="strategy",values="success")*100
axs[0].plot(e6b.index,e6b["AMS"],":",color=COL["AMS"],marker="s",mfc="white",ms=2.6,lw=1.0,label="AMS (S1)")
axs[0].plot(e6b.index,e6b["Hybrid-Med"],":",color=COL["Hybrid-Med"],marker="^",mfc="white",ms=2.6,lw=1.0,label="Hybrid-Med (S1)")
axs[0].set_xlabel("Transfer factor $\\chi$"); axs[0].set_ylabel("Success (%)"); axs[0].set_ylim(-4,108); axs[0].set_title("(a)",fontsize=7,pad=2)
axs[0].legend(frameon=False,fontsize=5.0,loc="center left",bbox_to_anchor=(0.0,0.55))
e7=d[d.exp=="E7b"]; rows=[]
for q,g in e7.groupby("outlier"):
    p=g.pivot_table(index=["maze","rep"],columns="strategy",values="time_ms")
    rows.append({"q":q,**{s:100*((p[s][(p[s]>0)&(p.Oracle>0)]/p.Oracle[(p[s]>0)&(p.Oracle>0)])-1).mean() for s in ["AMS","Hybrid","Hybrid-Med","Fixed-Safe"]}})
r=pd.DataFrame(rows).set_index("q")
for s in ["AMS","Hybrid","Hybrid-Med","Fixed-Safe"]: line(axs[1],r.index*100,r[s],s)
axs[1].set_xlabel("Outlier rate (%), S3"); axs[1].set_ylabel("Time vs. Oracle (%)"); axs[1].set_title("(b)",fontsize=7,pad=2)
axs[1].legend(frameon=False,fontsize=5.6,loc="upper left")
save(fig,"e67_transfer_outliers")

# ---- E8 discharge
fig,axs=plt.subplots(1,2,figsize=(3.45,1.85),sharey=True)
for a,exp,t in [(axs[0],"E8b","(a) $\\rho_P$=0"),(axs[1],"E8","(b) $\\rho_P$=10%")]:
    g=d[d.exp==exp].pivot_table(index="kappa",columns="strategy",values="success")*100
    for s in ["Fixed","VC","AMS","Hybrid-Med","Oracle"]: line(a,g.index*1e4,g[s],s)
    a.set_xlabel("Discharge $\\kappa$ ($10^{-4}$ s$^{-1}$)"); a.set_title(t,fontsize=7,pad=2)
axs[0].set_ylabel("Success (%)"); axs[0].set_ylim(-4,108)
h,l=axs[0].get_legend_handles_labels(); fig.legend(h,l,frameon=False,ncol=5,fontsize=5.8,loc="upper center",bbox_to_anchor=(0.5,1.07),handlelength=1.3,columnspacing=0.7)
fig.tight_layout(pad=0.3,rect=(0,0,1,0.92)); fig.savefig(f"{OUT}/e8_discharge.pdf",bbox_inches="tight",pad_inches=0.02); fig.savefig(f"{OUT}/e8_discharge.png",dpi=200,bbox_inches="tight",pad_inches=0.02); plt.close(fig)

# ---- analysis check
n=d[(d.exp=="E1")&(d.scen=="S0")&(d.strategy=="Fixed")].groupby("maze").steps.max().values
gam=1.02/0.98; bb=np.linspace(0.95,1.0,101)
pred=[np.mean(norm.cdf((gam*b-1)/0.01)**n)*100 for b in bb]
sim=d[(d.exp=="E4")&(d.tau==0)&(d.strategy=="Fixed")].groupby("b0").success.mean()*100
fig,ax=plt.subplots(figsize=(3.4,1.6))
ax.plot(bb,pred,"-",color=COL["Fixed"],lw=1.1,label="Closed-form prediction")
ax.plot(sim.index,sim.values,"o",color="#C44E52",ms=3.4,label="Simulation (500 trials/point)")
ax.axvline(1/gam,color="#888",lw=0.6,ls=":"); ax.text(1/gam-0.0007,55,"$1/(1+\\gamma)$",ha="right",fontsize=6)
ax.set_xlabel("Speed factor $b_0$"); ax.set_ylabel("Fixed success (%)"); ax.set_ylim(-4,108); ax.legend(frameon=False,fontsize=6.2,loc="upper left")
save(fig,"analysis_check")
# ---- E10 voltage sensor errors
fig,axs=plt.subplots(1,2,figsize=(3.45,1.8),sharey=True)
g=d[d.exp=="E10"].pivot_table(index="vgain",columns="strategy",values="success")*100
for st in ["VC","Hybrid-Med","Oracle"]: line(axs[0],(g.index-1)*100,g[st],st)
axs[0].set_xlabel("Voltage gain error (%), S1"); axs[0].set_ylabel("Success (%)"); axs[0].set_title("(a)",fontsize=7,pad=2); axs[0].set_ylim(-4,108)
g=d[d.exp=="E10n"].pivot_table(index="vnoise",columns="strategy",values="success")*100
for st in ["VC","AMS","Hybrid-Med","Oracle"]: line(axs[1],g.index*100,g[st],st)
axs[1].set_xlabel("Voltage noise (%), S1"); axs[1].set_title("(b)",fontsize=7,pad=2)
h,l=axs[1].get_legend_handles_labels(); fig.legend(h,l,frameon=False,ncol=4,fontsize=5.8,loc="upper center",bbox_to_anchor=(0.5,1.07),handlelength=1.3,columnspacing=0.7)
fig.tight_layout(pad=0.3,rect=(0,0,1,0.92)); fig.savefig(f"{OUT}/e10_sensor.pdf",bbox_inches="tight",pad_inches=0.02); fig.savefig(f"{OUT}/e10_sensor.png",dpi=200,bbox_inches="tight",pad_inches=0.02); plt.close(fig)
print("figs ok")
