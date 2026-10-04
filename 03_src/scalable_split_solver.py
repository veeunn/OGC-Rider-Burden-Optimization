from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
from itertools import permutations
import json, sys, time
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
BASELINE=ROOT/"02_baseline"/"runnable"
sys.path.insert(0,str(BASELINE))
from util import Order,Rider,get_total_distance,test_route_feasibility

@dataclass(frozen=True)
class RouteRecord:
    pickup_seq: tuple[int,...]
    delivery_seq: tuple[int,...]
    cost: float
    distance_m: float
    order_count: int
    active_route_duration_sec: float
    waiting_time_sec: float

@dataclass
class DecodedSolution:
    permutation: np.ndarray
    routes: list[RouteRecord]
    total_cost: float
    avg_cost: float
    @property
    def R0(self): return len(self.routes)
    def bundles(self):
        return [["BIKE",list(r.pickup_seq),list(r.delivery_seq)] for r in self.routes]

class BikeSplitProblem:
    def __init__(self,problem_path,max_route_size=4,route_cache_size=500000):
        self.problem_path=Path(problem_path)
        data=json.loads(self.problem_path.read_text(encoding="utf-8"))
        self.data=data; self.name=data.get("name",self.problem_path.stem); self.K=int(data["K"])
        self.orders=[Order(x) for x in data["ORDERS"]]
        bike_info=next(x for x in data["RIDERS"] if x[0]=="BIKE")
        self.rider=Rider(list(bike_info)); self.dist=np.asarray(data["DIST"])
        self.rider.T=np.round(self.dist/self.rider.speed+self.rider.service_time)
        self.ready=np.asarray([o.ready_time for o in self.orders],float)
        self.deadline=np.asarray([o.deadline for o in self.orders],float)
        self.volume=np.asarray([o.volume for o in self.orders],float)
        self.max_route_size=int(max_route_size)
        self._best_route=lru_cache(maxsize=int(route_cache_size))(self._best_route_uncached)

    def cache_info(self): return self._best_route.cache_info()

    def _pickup_clock(self,seq):
        if float(self.volume[list(seq)].sum())>float(self.rider.capa): return 0.0,0.0,False
        cur=seq[0]; t=float(self.ready[cur]); waiting=0.0
        for nxt in seq[1:]:
            tr=float(self.rider.T[cur,nxt]); arr=t+tr; w=max(0.0,float(self.ready[nxt])-arr)
            waiting+=w; t=max(arr,float(self.ready[nxt])); cur=nxt
        return t,waiting,True

    def _best_route_uncached(self,seq):
        if not seq or len(seq)>self.max_route_size: return None
        t0,waiting,ok=self._pickup_clock(seq)
        if not ok: return None
        K=self.K; active_pick=sum(float(self.rider.T[a,b]) for a,b in zip(seq[:-1],seq[1:]))
        best=None; best_key=None
        for dlv in permutations(seq):
            t=t0; active=active_pick
            first=dlv[0]; tr=float(self.rider.T[seq[-1],first+K]); t+=tr; active+=tr
            if t>float(self.deadline[first]): continue
            prev=first; feasible=True
            for nxt in dlv[1:]:
                tr=float(self.rider.T[prev+K,nxt+K]); t+=tr; active+=tr
                if t>float(self.deadline[nxt]): feasible=False; break
                prev=nxt
            if not feasible: continue
            dist=float(get_total_distance(K,self.dist,seq,dlv)); cost=float(self.rider.calculate_cost(dist))
            key=(cost,tuple(int(x) for x in dlv))
            if best is None or key<best_key:
                best_key=key
                best=RouteRecord(tuple(int(x) for x in seq),tuple(int(x) for x in dlv),cost,dist,len(seq),active,float(waiting))
        return best

    def best_route(self,pickup_seq): return self._best_route(tuple(int(x) for x in pickup_seq))

    def decode_cost(self,permutation):
        perm=np.asarray(permutation,dtype=np.int32)
        if perm.shape!=(self.K,) or np.unique(perm).size!=self.K: raise ValueError("invalid permutation")
        inf=float("inf"); dp=np.full(self.K+1,inf); prev=np.full(self.K+1,-1,dtype=np.int32); chosen=[None]*(self.K+1); dp[0]=0.0
        for end in range(1,self.K+1):
            for size in range(1,min(self.max_route_size,end)+1):
                start=end-size
                if not np.isfinite(dp[start]): continue
                route=self.best_route(tuple(perm[start:end]))
                if route is None: continue
                val=dp[start]+route.cost
                if val<dp[end]-1e-12:
                    dp[end]=val; prev[end]=start; chosen[end]=route
        if not np.isfinite(dp[self.K]): raise RuntimeError("No feasible Split partition")
        routes=[]; pos=self.K
        while pos>0:
            route=chosen[pos]
            if route is None: raise RuntimeError("Split reconstruction failure")
            routes.append(route); pos=int(prev[pos])
        routes.reverse()
        return DecodedSolution(perm.copy(),routes,float(dp[self.K]),float(dp[self.K]/self.K))

    def validate_decoded(self,sol):
        seen=[]
        for r in sol.routes:
            if test_route_feasibility(self.orders,self.rider,list(r.pickup_seq),list(r.delivery_seq))!=0:
                return {"feasible":False,"reason":"route infeasible"}
            seen.extend(r.pickup_seq)
        if sorted(seen)!=list(range(self.K)): return {"feasible":False,"reason":"coverage"}
        return {"feasible":True,"R0":sol.R0,"total_cost":sol.total_cost,"avg_cost":sol.avg_cost}

def order_crossover(rng,a,b):
    n=len(a); lo,hi=sorted(rng.integers(0,n,size=2))
    if lo==hi: hi=min(n,lo+1)
    child=np.full(n,-1,dtype=np.int32); child[lo:hi]=a[lo:hi]; used=set(map(int,child[lo:hi]))
    fill=[int(x) for x in b if int(x) not in used]; child[np.flatnonzero(child<0)]=fill
    return child

def mutate_permutation(rng,x,intensity=1):
    y=x.copy(); n=len(y)
    for _ in range(max(1,int(intensity))):
        i,j=sorted(rng.integers(0,n,size=2))
        if rng.random()<0.5: y[i],y[j]=y[j],y[i]
        elif j>i: y[i:j]=y[i:j][::-1]
    return y

def heuristic_permutations(problem):
    ids=np.arange(problem.K,dtype=np.int32)
    seeds=[ids[np.argsort(problem.ready,kind="stable")],ids[np.argsort(problem.deadline,kind="stable")],ids[np.lexsort((problem.deadline,problem.ready))],ids[np.lexsort((problem.ready,problem.deadline))]]
    out=[]; seen=set()
    for p in seeds:
        k=p.tobytes()
        if k not in seen: seen.add(k); out.append(p.copy())
    return out

def solve_s0_ga(problem,population_size=24,generations=30,seed=0,elite_fraction=0.25,crossover_probability=0.9):
    rng=np.random.default_rng(seed); started=time.time(); population=heuristic_permutations(problem); base=population[0]
    while len(population)<population_size:
        x=mutate_permutation(rng,base,max(1,problem.K//100)) if len(population)<max(6,population_size//3) else rng.permutation(problem.K).astype(np.int32)
        population.append(x)
    best=None; history=[]
    for gen in range(generations+1):
        evaluated=[]
        for p in population:
            try: sol=problem.decode_cost(p); evaluated.append((sol.avg_cost,sol))
            except RuntimeError: evaluated.append((float("inf"),None))
        order=np.argsort([v[0] for v in evaluated]); population=[population[int(i)] for i in order]; evaluated=[evaluated[int(i)] for i in order]
        if evaluated[0][1] is not None and (best is None or evaluated[0][0]<best.avg_cost): best=evaluated[0][1]
        feasible=sum(s is not None for _,s in evaluated); history.append({"generation":gen,"best_avg_cost":None if best is None else best.avg_cost,"feasible_population":feasible})
        print(f"[S0 split-GA] gen={gen} best={None if best is None else best.avg_cost} feasible={feasible}/{population_size}",flush=True)
        if gen==generations: break
        elite_n=max(2,int(round(population_size*elite_fraction))); elites=population[:elite_n]; nxt=[x.copy() for x in elites]
        while len(nxt)<population_size:
            pa=elites[int(rng.integers(0,elite_n))]; pb=population[int(rng.integers(0,max(elite_n,population_size//2)))]
            child=order_crossover(rng,pa,pb) if rng.random()<crossover_probability else pa.copy()
            nxt.append(mutate_permutation(rng,child,1 if problem.K<200 else max(1,problem.K//500)))
        population=nxt
    if best is None: raise RuntimeError("No feasible S0 solution")
    ci=problem.cache_info()
    return best,{"solver":"giant-tour-split-ga","seed":seed,"population_size":population_size,"generations":generations,"max_route_size":problem.max_route_size,"runtime_sec":time.time()-started,"cache":{"hits":ci.hits,"misses":ci.misses,"currsize":ci.currsize},"history":history}
