"""Tier-4 advanced designs on data in hand:
#7 matched case-control (removes size confounding),
#8 binomial 'lottery' test (is positivity just proportional to tower count?),
#3 spatial trend-surface / directional gradient (Moran's I is blind to gradients).
"""
import pathlib, io, math
import numpy as np, pandas as pd
from scipy import stats
import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
import warnings; warnings.filterwarnings("ignore")

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROC, REP = ROOT/"data"/"processed", ROOT/"reports"
OUT = io.StringIO()
def log(*a): print(*a); print(*a, file=OUT)

z = pd.read_csv(PROC/"analysis_table_pluto.csv")   # zone + PLUTO
for c in ["n_towers","n_samples_24mo","n_violations","days_since_last_inspection",
          "assesstot","bldgarea","bldg_age_yrs","reg_age_days","lat","lon","overdue_90d"]:
    z[c] = pd.to_numeric(z[c], errors="coerce")
z["log_assess"] = np.log10(z["assesstot"].where(z["assesstot"] > 0))
z["reg_age_yrs"] = z["reg_age_days"]/365.25

# ============ #7 MATCHED CASE-CONTROL (match on size/value/age) ============
log("="*66); log("#7  MATCHED CASE-CONTROL — remove building-size confounding")
log("="*66)
MATCH = ["log_assess","bldgarea","bldg_age_yrs","n_towers"]
mm = z.dropna(subset=MATCH).copy()
sc = StandardScaler(); MS = sc.fit_transform(mm[MATCH])
mm = mm.reset_index(drop=True); mm["_ms"] = list(MS)
cases = mm[mm.case == 1]; ctrls = mm[mm.case == 0].reset_index(drop=True)
nn = NearestNeighbors(n_neighbors=1).fit(np.vstack(ctrls["_ms"].values))
pairs = []
used = set()
for _, cr in cases.iterrows():
    d, idx = nn.kneighbors([cr["_ms"]], n_neighbors=min(5, len(ctrls)))
    for j in idx[0]:
        if j not in used:
            used.add(j); pairs.append((cr, ctrls.iloc[j])); break
log(f"matched pairs: {len(pairs)} (each case -> nearest unused control on size/value/age)")
# paired comparison of compliance predictors
COMP = ["n_samples_24mo","n_violations","days_since_last_inspection","overdue_90d","reg_age_yrs"]
log(f"\n{'compliance var':<26}{'case mean':>10}{'ctrl mean':>10}{'Wilcoxon p':>12}")
for c in COMP:
    cv = np.array([p[0][c] for p in pairs], float)
    kv = np.array([p[1][c] for p in pairs], float)
    ok = ~(np.isnan(cv) | np.isnan(kv))
    try: _, p = stats.wilcoxon(cv[ok], kv[ok])
    except Exception: p = np.nan
    log(f"{c:<26}{np.nanmean(cv):>10.2f}{np.nanmean(kv):>10.2f}{p:>12.4f}")
log("  -> With size matched, does any maintenance metric still separate case vs control?")

# ============ #8 BINOMIAL 'LOTTERY' TEST ============
log("\n" + "="*66); log("#8  LOTTERY MODEL — is positivity just proportional to # towers?")
log("="*66)
d8 = z.dropna(subset=["n_towers"]).copy(); n = d8["n_towers"].clip(lower=1).values; y = d8["case"].values
# MLE of per-tower prob p under building_pos = 1-(1-p)^n
from scipy.optimize import minimize_scalar
def negll(p):
    p = min(max(p,1e-6),1-1e-6); q = (1-p)**n; pr = 1-q
    pr = np.clip(pr,1e-9,1-1e-9)
    return -np.sum(y*np.log(pr)+(1-y)*np.log(1-pr))
res = minimize_scalar(negll, bounds=(1e-4,0.99), method="bounded")
phat = res.x; ll_lot = -res.fun
# null (constant prob, ignores towers)
p0 = y.mean(); ll_const = np.sum(y*np.log(p0)+(1-y)*np.log(1-p0))
log(f"  per-tower prob (MLE, lottery): p={phat:.3f}")
log(f"  logLik  lottery={ll_lot:.2f}   constant(ignore towers)={ll_const:.2f}")
lr = 2*(ll_lot-ll_const); pval = stats.chi2.sf(lr, 1)
log(f"  LR test lottery vs constant: chi2={lr:.2f}  p={pval:.3f}")
# direct logistic on log(n_towers)
Xt = sm.add_constant(np.log(n)); rt = sm.Logit(y, Xt).fit(disp=0)
log(f"  logistic case~log(#towers): OR={np.exp(rt.params[1]):.3f}  p={rt.pvalues[1]:.3f}")
log("  -> If tower count barely moves positivity, a pure 'more towers=more chances'"
    "\n     lottery is rejected: the action is per-tower conditions, not tower count.")

# ============ #3 SPATIAL TREND-SURFACE / DIRECTIONAL GRADIENT ============
log("\n" + "="*66); log("#3  DIRECTIONAL GRADIENT — trend-surface logistic (non-circular)")
log("="*66)
g = z.dropna(subset=["lat","lon"]).copy()
latm = g["lat"].mean()
g["x_km"] = (g["lon"]-g["lon"].mean())*111.32*math.cos(math.radians(latm))
g["y_km"] = (g["lat"]-g["lat"].mean())*110.57
Xg = sm.add_constant(g[["x_km","y_km"]]); rg = sm.Logit(g["case"].values, Xg).fit(disp=0)
log("  case ~ x_km (E-W) + y_km (N-S):")
for k in ["x_km","y_km"]:
    log(f"    {k}: OR/km={np.exp(rg.params[k]):.3f}  p={rg.pvalues[k]:.3f}")
# resultant direction/magnitude of the gradient
bx, by = rg.params["x_km"], rg.params["y_km"]
bearing = (math.degrees(math.atan2(bx, by))+360) % 360
log(f"  gradient magnitude={math.hypot(bx,by):.3f} /km, bearing={bearing:.0f}deg "
    f"(0=N,90=E); joint LLR p={rg.llr_pvalue:.3f}")
log("  -> Significant x/y = positivity rises in a direction (a gradient Moran's I misses).")

(REP/"stats_tier4_models.txt").write_text(OUT.getvalue())
log("\nwrote reports/stats_tier4_models.txt")
