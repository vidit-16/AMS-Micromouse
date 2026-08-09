// Micromouse drift-aware cost-model simulator, v3
// Builds on v2 (micromouse_sim_v2.cpp). Changes in v3:
//  * Braided mazes (loops) with an open 2x2 goal, so the time-optimal planner has real route choices.
//  * Realistic, separate exploration and speed-run primitive timings (ms per 180 mm cell / pivot).
//  * Non-uniform degradation: voltage factor 1/b (all primitives) times a per-primitive
//    residual factor (1+rho_m) for floor friction / heating that a voltage sensor cannot see.
//  * Exploration-to-speed transfer factor chi (how much of the speed-run slowdown is visible
//    at exploration speed) and optional outlier samples during exploration.
//  * The robot returns to the start cell after exploration; the speed run starts there.
//  * Voltage sensor model for VC/Hybrid: measured b = b * gain * (1 + noise).
//  * Strategies: Fixed, Fixed-Safe, VC (voltage-compensated), AMS (mean / median, threshold tau),
//    Hybrid (VC + learned residual; mean or median), Oracle (reference).
//
// Usage: ./build/micromouse_sim key=value ...   (see Params below for keys)

#include <bits/stdc++.h>
using namespace std;

constexpr array<int,4> dx = {0, 1, 0, -1};    // N,E,S,W
constexpr array<int,4> dy = {-1, 0, 1, 0};
constexpr int Nbit=1, Ebit=2, Sbit=4, Wbit=8;
constexpr array<int,4> opposite_wall = {Sbit, Wbit, Nbit, Ebit};
constexpr array<int,4> wall_bit = {Nbit, Ebit, Sbit, Wbit};
enum Prim { F=0, U=1, R=2, L=3 };
const char* PNAME[4]={"F","U","R","L"};

struct Params {
    int nmazes=100, reps=10, W=16, H=16;
    double braid=0.10;                 // fraction of remaining interior walls removed
    double b0=1.0, kappa=0.0;          // b(T)=max(0.3, b0 - kappa*T[s])
    double rhoF=0.0, rhoP=0.0;         // residual slowdown, forward / pivots
    double sigma=0.01, margin=0.02, safe_margin=0.35;
    double tau=0.0;                    // AMS drift threshold (%)
    double chi=1.0;                    // exploration transfer factor
    double outlier=0.0;                // probability an exploration sample is an outlier
    double vgain=1.0, vnoise=0.0;      // voltage-sensor gain error and relative noise (VC, Hybrid)
    array<double,4> cS{100,300,180,180};   // speed-run costs (ms): F, U, R, L
    array<double,4> cE{300,540,360,360};   // exploration costs (ms)
};

struct Maze {
    int W,H; vector<int> w; // walls bitmask per cell
    int& at(int x,int y){return w[y*W+x];} int get(int x,int y) const {return w[y*W+x];}
    bool open(int x,int y,int d) const {return !(get(x,y)&wall_bit[d]);}
    void removeWall(int x,int y,int d){ at(x,y)&=~wall_bit[d]; at(x+dx[d],y+dy[d])&=~opposite_wall[d]; }
    Maze(int W_,int H_,uint32_t seed,double braid):W(W_),H(H_),w(W_*H_,0xF){
        mt19937 g(seed);
        vector<char> vis(W*H,0); stack<pair<int,int>> st;
        vis[0]=1; vis[1]=1; removeWall(0,0,1); st.push({1,0});   // 3-wall start, open East
        while(!st.empty()){
            auto [cx,cy]=st.top(); vector<int> nb;
            for(int d=0;d<4;d++){int nx=cx+dx[d],ny=cy+dy[d]; if(nx>=0&&nx<W&&ny>=0&&ny<H&&!vis[ny*W+nx]) nb.push_back(d);}
            if(nb.empty()){st.pop();continue;}
            shuffle(nb.begin(),nb.end(),g); int d=nb[0]; removeWall(cx,cy,d); vis[(cy+dy[d])*W+cx+dx[d]]=1; st.push({cx+dx[d],cy+dy[d]});
        }
        int gx=W/2-1, gy=H/2-1;
        removeWall(gx,gy,1); removeWall(gx,gy,2); removeWall(gx+1,gy,2); removeWall(gx,gy+1,1); // open 2x2 goal
        // braid: remove a fraction of remaining interior walls (never around the start cell)
        vector<tuple<int,int,int>> cand;
        for(int y=0;y<H;y++) for(int x=0;x<W;x++) for(int d: {1,2}){
            int nx=x+dx[d], ny=y+dy[d]; if(nx>=W||ny>=H) continue;
            if(!(get(x,y)&wall_bit[d])) continue;
            if((x==0&&y==0)||(nx==0&&ny==0)) continue;
            cand.push_back({x,y,d});
        }
        shuffle(cand.begin(),cand.end(),g);
        int k=(int)llround(braid*cand.size());
        for(int i=0;i<k;i++){auto [x,y,d]=cand[i]; removeWall(x,y,d);}
    }
};

struct Plan { vector<int> prims; vector<array<int,3>> states; double pred=0; };

// Dijkstra on (x,y,theta) from the goal region; returns time-to-goal for all states.
vector<double> timeField(const Maze& m, const array<double,4>& c){
    int W=m.W,H=m.H; vector<double> T(W*H*4,1e18);
    priority_queue<tuple<double,int,int,int>,vector<tuple<double,int,int,int>>,greater<>> pq;
    int gx=W/2-1, gy=H/2-1;
    for(int y=gy;y<=gy+1;y++) for(int x=gx;x<=gx+1;x++) for(int o=0;o<4;o++){T[(y*W+x)*4+o]=0; pq.push({0,x,y,o});}
    while(!pq.empty()){
        auto [t,x,y,o]=pq.top(); pq.pop(); if(t>T[(y*W+x)*4+o]) continue;
        // predecessor A: same cell, pivot into o from o' (cost of pivot)
        for(int po=0;po<4;po++) if(po!=o){
            int d=(o-po+4)%4; double pc = d==1?c[R]: d==3?c[L]: c[U];
            double nt=t+pc; int id=(y*W+x)*4+po; if(nt<T[id]){T[id]=nt; pq.push({nt,x,y,po});}
        }
        // predecessor B: came forward from the cell behind, facing o
        int px=x-dx[o], py=y-dy[o];
        if(px>=0&&px<W&&py>=0&&py<H&&m.open(px,py,o)){
            double nt=t+c[F]; int id=(py*W+px)*4+o; if(nt<T[id]){T[id]=nt; pq.push({nt,px,py,o});}
        }
    }
    return T;
}
Plan extractPlan(const Maze& m,const vector<double>& T,const array<double,4>& c,int x,int y,int o){
    Plan p; int W=m.W,H=m.H,gx=W/2-1,gy=H/2-1; p.pred=T[(y*W+x)*4+o];
    for(int it=0; it<4*W*H*4; it++){
        if(x>=gx&&x<=gx+1&&y>=gy&&y<=gy+1) break;
        double cur=T[(y*W+x)*4+o]; int best=-1; double bv=1e18; int bx=x,by=y,bo=o;
        if(m.open(x,y,o)){int nx=x+dx[o],ny=y+dy[o]; double v=c[F]+T[(ny*W+nx)*4+o]; if(v<bv-1e-9){bv=v;best=F;bx=nx;by=ny;bo=o;}}
        for(int d: {1,3,2}){int no=(o+d)%4; double pc= d==1?c[R]: d==3?c[L]: c[U]; double v=pc+T[(y*W+x)*4+no];
            if(v<bv-1e-9){bv=v;best= d==1?R: d==3?L: U; bx=x;by=y;bo=no;}}
        if(best<0||bv>cur+1e-6) throw runtime_error("plan extraction failed");
        p.prims.push_back(best); p.states.push_back({bx,by,bo}); x=bx;y=by;o=bo;
    }
    return p;
}
double planCost(const Plan& p,const array<double,4>& c){double s=0; for(int q:p.prims) s+=c[q]; return s;}

struct World {
    const Params& P; mt19937 rng; normal_distribution<double> nd{0,1}; uniform_real_distribution<double> ud{0,1};
    double T=0; // elapsed motion time (ms)
    mt19937 vrng; normal_distribution<double> vnd{0,1};
    World(const Params& p,uint32_t seed):P(p),rng(seed),vrng(seed^0x9E3779B9u){}
    double bMeas(){ double e = P.vnoise>0 ? P.vnoise*vnd(vrng) : 0.0; return b()*P.vgain*(1.0+e); }
    double b() const { return max(0.3, P.b0 - P.kappa*T/1000.0); }
    double rho(int q) const { return q==F?P.rhoF:P.rhoP; }
    double trueFactor(int q) const { return (1.0/b())*(1.0+rho(q)); }
    double noise(){ return P.sigma>0? max(-0.5,P.sigma*nd(rng)) : 0.0; }
    // exploration (closed-loop, slower): factor partially visible (chi), optional outlier
    double exploreTime(int q){
        double g=1.0+P.chi*(trueFactor(q)-1.0);
        double t=P.cE[q]*g*(1.0+noise());
        if(P.outlier>0 && ud(rng)<P.outlier) t*=1.0+0.5+1.5*ud(rng);
        return t;
    }
    double speedReq(int q){ return P.cS[q]*trueFactor(q)*(1.0+noise()); }
};

enum Strat { FIXED=0, SAFE, VC, AMS, AMSM, HYBRID, ORACLE, HYBRIDM, NSTRAT };
const char* SNAME[NSTRAT]={"Fixed","Fixed-Safe","VC","AMS","AMS-Med","Hybrid","Oracle","Hybrid-Med"};

struct Res { bool ok=false; double time=0, explore=0; int steps=0, fail_step=-1; bool switched=false, replanned=false;
             double replan_gain=0, ff_gain=0, maxdrift=0, b_run=0; array<double,4> est{}; array<int,4> n{}; };

// ---- exploration with memory map (conservative BFS over confirmed-open edges) ----
struct Explorer {
    const Maze& m; int W,H; vector<int> mem; vector<char> vis; int x=0,y=0,o=1;
    Explorer(const Maze& mm):m(mm),W(mm.W),H(mm.H),mem(W*H,0xF),vis(W*H,0){}
    void sense(){ int w=m.get(x,y); mem[y*W+x]=w; vis[y*W+x]=1;
        for(int d=0;d<4;d++){int nx=x+dx[d],ny=y+dy[d]; if(nx<0||nx>=W||ny<0||ny>=H) continue;
            if(w&wall_bit[d]) mem[ny*W+nx]|=opposite_wall[d]; else mem[ny*W+nx]&=~opposite_wall[d];}}
    // next primitive toward target chosen by f(dist,visited); returns -1 when none
    int stepToward(function<bool(int,int)> isTarget){
        vector<int> dist(W*H,-1); queue<int> q; q.push(y*W+x); dist[y*W+x]=0; int tgt=-1;
        while(!q.empty()){int c=q.front();q.pop(); int cx=c%W,cy=c/W; if(c!=y*W+x && isTarget(cx,cy)){tgt=c;break;}
            for(int d=0;d<4;d++){ if(mem[c]&wall_bit[d]) continue; int nx=cx+dx[d],ny=cy+dy[d];
                if(nx<0||nx>=W||ny<0||ny>=H) continue; int n=ny*W+nx; if(dist[n]<0){dist[n]=dist[c]+1;q.push(n);}}}
        if(tgt<0) return -1;
        int c=tgt;
        while(dist[c]>1){int cx=c%W,cy=c/W; for(int d=0;d<4;d++){ if(mem[c]&wall_bit[d]) continue;
            int nx=cx+dx[d],ny=cy+dy[d]; if(nx<0||nx>=W||ny<0||ny>=H) continue; int n=ny*W+nx; if(dist[n]==dist[c]-1){c=n;break;}}}
        int nx=c%W,ny=c/W, to= ny<y?0: nx>x?1: ny>y?2:3; int d=(to-o+4)%4;
        return d==0?F: d==1?R: d==3?L: U;
    }
    void apply(int q){ if(q==F){x+=dx[o];y+=dy[o];} else if(q==R) o=(o+1)%4; else if(q==L) o=(o+3)%4; else o=(o+2)%4; }
};

Res runTrial(const Maze& m,int strat,const Params& P,uint32_t seed,vector<pair<int,int>>* etrace=nullptr,Plan* outPlan=nullptr){
    World w(P,seed); Explorer e(m); Res r;
    vector<vector<double>> ratio(4), resid(4);  // AMS ratios; Hybrid residuals (voltage-normalised)
    auto record=[&](int q){ double t=w.exploreTime(q); double bm=w.bMeas(); w.T+=t; r.explore+=t;
        ratio[q].push_back(t/P.cE[q]); resid[q].push_back(t/P.cE[q]*bm); e.apply(q); if(etrace) etrace->push_back({e.x,e.y}); };
    int gx=m.W/2-1, gy=m.H/2-1;
    // phase 1: explore every reachable cell
    for(int it=0; it<200000; it++){ e.sense(); int q=e.stepToward([&](int cx,int cy){return !e.vis[cy*e.W+cx];}); if(q<0) break; record(q); }
    // phase 2: return to start (closed-loop, also measured)
    for(int it=0; it<20000 && !(e.x==0&&e.y==0); it++){ e.sense(); int q=e.stepToward([&](int cx,int cy){return cx==0&&cy==0;}); if(q<0) break; record(q); }
    if(!(e.x==0&&e.y==0)) throw runtime_error("did not return to start");
    for(int i=0;i<m.W*m.H;i++) if(e.mem[i]!=m.w[i]) throw runtime_error("map mismatch");
    // ---- cost model for the speed run ----
    array<double,4> est; array<double,4> factor; factor.fill(1.0);
    auto agg=[&](vector<double>& v,bool median)->double{ if(v.empty()) return NAN; if(!median) return accumulate(v.begin(),v.end(),0.0)/v.size();
        vector<double> s=v; nth_element(s.begin(),s.begin()+s.size()/2,s.end()); return s[s.size()/2]; };
    if(strat==AMS||strat==AMSM||strat==HYBRID||strat==HYBRIDM){
        bool med = (strat==AMSM||strat==HYBRIDM); auto& src = (strat==HYBRID||strat==HYBRIDM)? resid : ratio;
        double sum=0; int k=0;
        for(int q=0;q<4;q++){ est[q]=agg(src[q],med); r.n[q]=src[q].size(); if(!isnan(est[q])){sum+=est[q];k++;} }
        for(int q=0;q<4;q++) if(isnan(est[q])) est[q]=sum/k;
        if(strat==HYBRID||strat==HYBRIDM) for(int q=0;q<4;q++) est[q]=max(1.0,est[q]);   // residual cannot speed the robot up
        r.est=est;
        for(int q=0;q<4;q++) r.maxdrift=max(r.maxdrift,100.0*fabs(est[q]-1.0));
        r.switched = (strat==HYBRID||strat==HYBRIDM) || r.maxdrift>P.tau;
        if(r.switched) factor=est;
    }
    // planning cost table (VC/Oracle scale with current state at command time; plan with start-of-run state)
    array<double,4> planC;
    for(int q=0;q<4;q++){
        double f=factor[q];
        if(strat==VC) f=1.0/w.bMeas();
        if(strat==HYBRID||strat==HYBRIDM) f=factor[q]/w.bMeas();
        if(strat==ORACLE) f=w.trueFactor(q);
        planC[q]=P.cS[q]*f;
    }
    auto T=timeField(m,planC); Plan plan=extractPlan(m,T,planC,e.x,e.y,e.o);
    {   // re-planning effect: compare with the path the fixed table would choose, both evaluated under planC
        auto Tf=timeField(m,P.cS); Plan pf=extractPlan(m,Tf,P.cS,e.x,e.y,e.o);
        double a=planCost(plan,planC), bcost=planCost(pf,planC);
        r.replanned = pf.prims!=plan.prims; r.replan_gain = 100.0*(bcost-a)/bcost;
        array<double,4> cc{1.0,1e-3,1e-3,1e-3};          // cell-count shortest path (flood-fill style), fewest turns on ties
        auto Tc=timeField(m,cc); Plan pc=extractPlan(m,Tc,cc,e.x,e.y,e.o);
        double ccost=planCost(pc,planC); r.ff_gain=100.0*(ccost-a)/ccost;
    }
    if(outPlan) *outPlan=plan;
    r.b_run=w.b();
    // ---- speed run ----
    for(size_t i=0;i<plan.prims.size();i++){
        int q=plan.prims[i]; double c;
        switch(strat){
            case FIXED: c=P.cS[q]*(1+P.margin); break;
            case SAFE:  c=P.cS[q]*(1+P.safe_margin); break;
            case VC:    c=P.cS[q]/w.bMeas()*(1+P.margin); break;
            case HYBRID: case HYBRIDM: c=P.cS[q]*factor[q]/w.bMeas()*(1+P.margin); break;
            case ORACLE:c=P.cS[q]*w.trueFactor(q)*(1+P.margin); break;
            default:    c=P.cS[q]*factor[q]*(1+P.margin);
        }
        double req=w.speedReq(q);
        if(c<0.98*req){ r.ok=false; r.fail_step=i; return r; }
        double t=max(c,req); w.T+=t; r.time+=t; r.steps++;
    }
    r.ok=true; return r;
}

int main(int argc,char** argv){
    Params P; string mode="run"; int trace_maze=0;
    for(int i=1;i<argc;i++){ string a=argv[i]; auto e=a.find('='); string k=a.substr(0,e), v=e==string::npos?"":a.substr(e+1);
        if(k=="mode") mode=v; else if(k=="nmazes") P.nmazes=stoi(v); else if(k=="reps") P.reps=stoi(v);
        else if(k=="braid") P.braid=stod(v); else if(k=="b0") P.b0=stod(v); else if(k=="kappa") P.kappa=stod(v);
        else if(k=="rhoF") P.rhoF=stod(v); else if(k=="rhoP") P.rhoP=stod(v); else if(k=="sigma") P.sigma=stod(v);
        else if(k=="margin") P.margin=stod(v); else if(k=="safe") P.safe_margin=stod(v); else if(k=="tau") P.tau=stod(v);
        else if(k=="chi") P.chi=stod(v); else if(k=="outlier") P.outlier=stod(v); else if(k=="vgain") P.vgain=stod(v); else if(k=="vnoise") P.vnoise=stod(v); else if(k=="maze") trace_maze=stoi(v);
        else { cerr<<"unknown key "<<k<<"\n"; return 1; } }
    if(mode=="trace"){
        Maze m(P.W,P.H,trace_maze,P.braid); vector<pair<int,int>> et; Plan pl;
        Params Q=P; Q.sigma=0; runTrial(m,FIXED,Q,1,&et,&pl);
        cout<<"WALLS"; for(int v:m.w) cout<<","<<v; cout<<"\nEXPLORE"; for(auto&c:et) cout<<","<<c.first<<":"<<c.second;
        cout<<"\nRUN,0:0"; for(auto&s:pl.states) cout<<","<<s[0]<<":"<<s[1]; cout<<"\n"; return 0;
    }
    vector<Maze> mazes; for(int i=0;i<P.nmazes;i++) mazes.emplace_back(P.W,P.H,(uint32_t)i,P.braid);
    cout<<"maze,rep,strategy,success,time_ms,steps,fail_step,explore_ms,switched,replanned,replan_gain,ff_gain,max_drift,b_run,est_F,est_U,est_R,est_L,n_F,n_U,n_R,n_L\n";
    for(int i=0;i<P.nmazes;i++) for(int k=0;k<P.reps;k++){
        uint32_t seed=1000003u*(uint32_t)i+7919u*(uint32_t)k+17u;   // common random numbers across strategies
        for(int s=0;s<NSTRAT;s++){
            Res r=runTrial(mazes[i],s,P,seed);
            cout<<i<<","<<k<<","<<SNAME[s]<<","<<r.ok<<","<<(r.ok?r.time:0)<<","<<r.steps<<","<<r.fail_step<<","<<r.explore<<","
                <<r.switched<<","<<r.replanned<<","<<r.replan_gain<<","<<r.ff_gain<<","<<r.maxdrift<<","<<r.b_run;
            for(int q=0;q<4;q++) cout<<","<<r.est[q]; for(int q=0;q<4;q++) cout<<","<<r.n[q]; cout<<"\n";
        }
    }
}
