"""Tier-5 further angles testable with public city data:
#1 local hotspot (Getis-Ord Gi*) + nearest-neighbour clustering (Ripley-style),
#2 is the sampling-frequency signal a PRIOR-PROBLEM marker (mandated re-testing)?
#3 initial-31 vs added-45 as an epicenter probe,
#4 remediation-speed outcome,
#5 retrospective power analysis,
#6 relative building height, #8 distance to Central Park (5th Ave edge).
"""
import json, math, pathlib, io
import numpy as np, pandas as pd
from scipy import stats
import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler
import warnings; warnings.filterwarnings("ignore")

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW, PROC, REP = ROOT/"data"/"raw", ROOT/"data"/"processed", ROOT/"reports"
OUT = io.StringIO()
def log(*a): print(*a); print(*a, file=OUT)

base = pd.read_csv(PROC/"analysis_table.csv"); base["bin"] = base["bin"].astype(str)
t1 = pd.read_csv(PROC/"analysis_table_tier1.csv"); t1["bin"] = t1["bin"].astype(str)
pl = pd.read_csv(PROC/"analysis_table_pluto.csv"); pl["bin"] = pl["bin"].astype(str)
z = base[base.in_outbreak_zip == 1].copy()
z = z.merge(t1[["bin","n_wq_viol","ever_wq_viol","n_noncycle"]], on="bin", how="left")
z = z.merge(pl[["bin","assesstot","bldgarea","bldg_age_yrs","numfloors"]], on="bin", how="left")
for c in ["n_towers","n_samples_24mo","n_violations","days_since_last_inspection",
          "assesstot","bldgarea","bldg_age_yrs","numfloors","lat","lon","n_wq_viol"]:
    z[c] = pd.to_numeric(z[c], errors="coerce")
z["log_assess"] = np.log10(z["assesstot"].where(z["assesstot"] > 0))
latm = z["lat"].mean()
z["x_km"] = (z["lon"]-z["lon"].mean())*111.32*math.cos(math.radians(latm))
z["y_km"] = (z["lat"]-z["lat"].mean())*110.57
g = z.dropna(subset=["lat","lon"]).reset_index(drop=True)
X = g["x_km"].values*1000; Y = g["y_km"].values*1000; C = g["case"].values.astype(float)
D = np.sqrt((X[:,None]-X[None,:])**2 + (Y[:,None]-Y[None,:])**2)

# ===== #1 Getis-Ord Gi* (local hotspots) =====
log("="*66); log("#1  LOCAL HOTSPOTS — Getis-Ord Gi* (300 m band) + NN clustering")
log("="*66)
band = 300.0; W = (D <= band).astype(float)  # include self
n = len(C); xbar = C.mean(); S = math.sqrt((C**2).mean()-xbar**2)
Wi = W.sum(1); num = W@C - xbar*Wi
den = S*np.sqrt((n*(W**2).sum(1)-Wi**2)/(n-1))
Gi = num/den
zmax = np.nanmax(Gi)
# permutation null for the max Gi* (controls multiple testing)
rng = np.random.default_rng(0); mx = []
for _ in range(999):
    cp = rng.permutation(C); nu = W@cp - cp.mean()*Wi
    de = math.sqrt((cp**2).mean()-cp.mean()**2)*np.sqrt((n*(W**2).sum(1)-Wi**2)/(n-1))
    mx.append(np.nanmax(nu/de))
p_hot = (1+sum(m >= zmax for m in mx))/(1000)
log(f"  max Gi* z = {zmax:.2f}  (permutation p for a hotspot = {p_hot:.3f})")
log(f"  buildings with Gi* z>1.96: {int((Gi>1.96).sum())}  (uncorrected)")
# nearest-neighbour clustering of positives vs random subsets
def mean_nn(mask):
    idx = np.where(mask)[0]; sub = D[np.ix_(idx,idx)].copy(); np.fill_diagonal(sub, np.inf)
    return sub.min(1).mean()
obs = mean_nn(C==1); rng2 = np.random.default_rng(1)
sims = [mean_nn(np.isin(np.arange(n), rng2.choice(n, int(C.sum()), replace=False))) for _ in range(999)]
p_nn = (1+sum(s <= obs for s in sims))/1000
log(f"  positives mean nearest-neighbour dist = {obs:.0f} m; random = {np.mean(sims):.0f} m; "
    f"clustering p = {p_nn:.3f}")

# ===== #2 Is sampling frequency a PRIOR-PROBLEM marker? =====
log("\n" + "="*66); log("#2  SAMPLING FREQUENCY — detection, or mandated re-testing after a prior fail?")
log("="*66)
rho1, p1 = stats.spearmanr(z["n_samples_24mo"], z["n_wq_viol"], nan_policy="omit")
rho2, p2 = stats.spearmanr(z["n_samples_24mo"], z["n_violations"], nan_policy="omit")
log(f"  Spearman(n_samples_24mo, water-quality violations) = {rho1:.2f} (p={p1:.3f})")
log(f"  Spearman(n_samples_24mo, total violations)         = {rho2:.2f} (p={p2:.3f})")
d = z.dropna(subset=["n_samples_24mo","n_wq_viol"]).copy()
for label, preds in [("case ~ sampling", ["n_samples_24mo"]),
                     ("case ~ sampling + prior water-quality viol", ["n_samples_24mo","n_wq_viol"])]:
    Xs = pd.DataFrame(StandardScaler().fit_transform(d[preds]), columns=preds, index=d.index)
    r = sm.Logit(d["case"].values, sm.add_constant(Xs)).fit(disp=0)
    log(f"  {label:<44} sampling OR/SD={np.exp(r.params['n_samples_24mo']):.2f} "
        f"p={r.pvalues['n_samples_24mo']:.3f}")
log("  -> If sampling stays strong after controlling for prior violations, it's detection,"
    "\n     not merely a prior-problem proxy.")

# ===== #3 initial-31 vs added-45 (epicenter probe) =====
log("\n" + "="*66); log("#3  INITIAL 31 vs ADDED 45 — where did the investigation start?")
log("="*66)
orig = z["status_group"].isin(["A_doh0710_complete","B_doh0710_expected"])
gg = z[z.case == 1].copy(); gg["orig"] = orig
o = gg[gg.orig]; a = gg[~gg.orig]
log(f"  initial-31 in zone: {len(o)}   added-45 in zone: {len(a)}")
for c in ["y_km","x_km"]:
    _, p = stats.mannwhitneyu(o[c].dropna(), a[c].dropna())
    log(f"  {c}: initial mean={o[c].mean():+.3f}  added mean={a[c].mean():+.3f}  (p={p:.3f})")
log(f"  (y_km +north/-south, x_km +east/-west; separation locates the epicenter)")

# ===== #4 remediation speed =====
log("\n" + "="*66); log("#4  REMEDIATION SPEED — what predicts 'completed' vs 'ordered-by-date'?")
log("="*66)
comp = z["status_group"].isin(["A_doh0710_complete","C_added_complete","E_unregistered_complete"])
cc = z[z.case == 1].copy(); cc["completed"] = comp[z.case == 1].values
preds = ["log_assess","n_towers","bldg_age_yrs"]
dd = cc.dropna(subset=preds+["completed"]).copy()
Xs = pd.DataFrame(StandardScaler().fit_transform(dd[preds]), columns=preds, index=dd.index)
r = sm.Logit(dd["completed"].astype(int).values, sm.add_constant(Xs)).fit(disp=0)
log(f"  completed={int(dd.completed.sum())}/{len(dd)} cases; logistic OR per 1 SD:")
for k in preds:
    log(f"    {k:<14} OR={np.exp(r.params[k]):.2f}  p={r.pvalues[k]:.3f}")

# ===== #5 retrospective power =====
log("\n" + "="*66); log("#5  RETROSPECTIVE POWER — smallest effect we could have detected")
log("="*66)
ncase, nctrl = int(z.case.sum()), int((z.case==0).sum()); N = ncase+nctrl; prev = ncase/N
rng3 = np.random.default_rng(3)
def power(orv, reps=400):
    b = math.log(orv); hit = 0
    for _ in range(reps):
        xp = rng3.standard_normal(N); lp = math.log(prev/(1-prev)) + b*xp
        yy = (rng3.random(N) < 1/(1+np.exp(-lp))).astype(int)
        if len(set(yy)) < 2: continue
        try:
            rr = sm.Logit(yy, sm.add_constant(xp)).fit(disp=0)
            if rr.pvalues[1] < 0.05: hit += 1
        except Exception: pass
    return hit/reps
for orv in [1.3,1.5,1.8,2.0,2.5]:
    log(f"  true OR/SD={orv}: power={power(orv):.0%}")
log(f"  (n={N}, {ncase} cases) -> effects below the ~80%-power OR are undetectable here.")

# ===== #6 relative building height =====
log("\n" + "="*66); log("#6  RELATIVE HEIGHT — taller than neighbours (dispersal advantage)?")
log("="*66)
nf = g["numfloors"].values
Wn = (D <= 200) & (D > 0)
relh = np.array([nf[i]-np.nanmean(nf[Wn[i]]) if Wn[i].any() else np.nan for i in range(n)])
g2 = g.assign(rel_height=relh)
aa = g2.loc[g2.case==1,"rel_height"].dropna(); bb = g2.loc[g2.case==0,"rel_height"].dropna()
_, p = stats.mannwhitneyu(aa, bb)
log(f"  floors above local (200 m) mean: case={aa.median():+.1f}  control={bb.median():+.1f}  p={p:.3f}")

# ===== #8 distance to Central Park (5 Av centerline) =====
log("\n" + "="*66); log("#8  DISTANCE TO CENTRAL PARK (5th-Ave edge)")
log("="*66)
fifth = []
try:
    for f in json.load(open(RAW/"ues_streets.geojson"))["features"]:
        if (f.get("properties") or {}).get("street_name") == "5":
            gm = f["geometry"]
            lines = [gm["coordinates"]] if gm["type"]=="LineString" else gm["coordinates"]
            for ln in lines: fifth += ln
except FileNotFoundError: pass
if fifth:
    fx = np.array([(p[0]-z["lon"].mean())*111320*math.cos(math.radians(latm)) for p in fifth])
    fy = np.array([(p[1]-z["lat"].mean())*110570 for p in fifth])
    dpark = np.array([np.sqrt((X[i]-fx)**2+(Y[i]-fy)**2).min() for i in range(n)])
    gp = g.assign(dist_park_m=dpark)
    aa = gp.loc[gp.case==1,"dist_park_m"]; bb = gp.loc[gp.case==0,"dist_park_m"]
    _, p = stats.mannwhitneyu(aa, bb)
    log(f"  distance to 5th Ave/park: case_med={aa.median():.0f} m  control_med={bb.median():.0f} m  p={p:.3f}")
else:
    log("  (5th-Ave geometry unavailable)")

(REP/"stats_tier5.txt").write_text(OUT.getvalue())
log("\nwrote reports/stats_tier5.txt")
