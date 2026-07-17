"""Tier-1 additional predictors for the outbreak-zone case-control analysis.

Tests hypotheses the base model couldn't: does the *right kind* of violation
(Legionella / water-quality, or high-severity) predict positivity? Do denser
tower clusters, follow-up inspections, building type, or irregular sampling?
All features capped pre-outbreak (2026-07-01); primary sample = outbreak ZIPs.
"""
import json, csv, math, pathlib, io
import numpy as np, pandas as pd
from datetime import date, datetime
from collections import defaultdict
from scipy import stats
import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
import warnings; warnings.filterwarnings("ignore")

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW, PROC, REP = ROOT/"data"/"raw", ROOT/"data"/"processed", ROOT/"reports"
REF, CUTOFF = date(2026, 7, 2), date(2026, 7, 1)
OUT = io.StringIO()
def log(*a): print(*a); print(*a, file=OUT)
def nb(b): b = (b or "").strip(); return b[:-2] if b.endswith(".0") else b
def piso(s):
    try: return datetime.fromisoformat((s or "").replace("Z", "")).date()
    except: return None
def pmdy(s):
    try: return datetime.strptime(s.strip(), "%m/%d/%Y").date()
    except: return None

base = pd.read_csv(PROC/"analysis_table.csv")
base["bin"] = base["bin"].astype(str)

# ---- all-Manhattan building coords (for local tower density) ----
coords = {str(r.bin): (r.lat, r.lon) for r in base.itertuples()
          if pd.notna(r.lat) and pd.notna(r.lon)}
def meters(a, b):
    (la1, lo1), (la2, lo2) = a, b
    R, m = 6371000.0, math.radians
    x = (m(lo2)-m(lo1))*math.cos(m((la1+la2)/2)); y = m(la2)-m(la1)
    return R*math.hypot(x, y)
def density(bn, radius=200):
    if bn not in coords: return np.nan
    c = coords[bn]; n = 0
    for o, oc in coords.items():
        if o != bn and meters(c, oc) <= radius: n += 1
    return n

# ---- inspection-derived severity / type / legionella features (pre-cutoff) ----
WQ = ("bacter", "legionella", "water quality", "water treatment", "disinfect",
      "corrective action", "sample", "monitor")
insp = json.load(open(RAW/"inspections.json"))
ins = defaultdict(lambda: {"phh": 0, "crit": 0, "wq": 0, "noncycle": 0, "inactive": False})
for r in insp:
    b = nb(r.get("bin"))
    if b not in coords: continue
    d = piso(r.get("inspection_date"))
    if not d or d >= CUTOFF: continue
    x = ins[b]
    vt = (r.get("violation_type") or "").strip()
    code = (r.get("violation_code") or "").strip()
    txt = (r.get("violation_text") or "").lower()
    if code:
        if vt == "PHH": x["phh"] += 1
        if vt == "Critical": x["crit"] += 1
        if any(w in txt for w in WQ): x["wq"] += 1
    if (r.get("inspection_type") or "") == "Non-Cycle": x["noncycle"] += 1
    if (r.get("status") or "").lower() == "inactive": x["inactive"] = True

# ---- registration sampling-cadence regularity (CV of gaps) ----
reg = json.load(open(RAW/"registrations.json"))
samp = defaultdict(list)
for r in reg:
    if r.get("borough") != "Manhattan": continue
    b = nb(r.get("bin"))
    for sd in (r.get("sampledates") or "").split(","):
        d = pmdy(sd)
        if d and d < CUTOFF: samp[b].append(d)
def gap_cv(bn):
    ds = sorted(set(samp.get(bn, [])))
    if len(ds) < 3: return np.nan
    g = np.array([(ds[i]-ds[i-1]).days for i in range(1, len(ds))], float)
    return g.std()/g.mean() if g.mean() > 0 else np.nan

# ---- PLUTO land use (zone) ----
pl = {}
try:
    for r in json.load(open(RAW/"pluto_zone.json")):
        pl[str(r["bbl"]).split(".")[0]] = r
    bin2bbl = json.load(open(PROC/"bin2bbl_zone.json"))
except FileNotFoundError:
    bin2bbl = {}
LU = {"01":"1-2 family","02":"walk-up","03":"walk-up","04":"mixed res/com",
      "05":"mixed res/com","06":"walk-up","07":"rentals","08":"co-op/condo",
      "09":"co-op/condo","10":"elevator apt","11":"special","13":"loft",
      "14":"loft"}  # coarse; PLUTO landuse codes

# ---- assemble zone table ----
z = base[base.in_outbreak_zip == 1].copy()
z["tower_density_200m"] = z["bin"].map(lambda b: density(b, 200))
z["n_phh_viol"]   = z["bin"].map(lambda b: ins.get(b, {}).get("phh", 0))
z["n_crit_viol"]  = z["bin"].map(lambda b: ins.get(b, {}).get("crit", 0))
z["n_wq_viol"]    = z["bin"].map(lambda b: ins.get(b, {}).get("wq", 0))
z["ever_wq_viol"] = (z["n_wq_viol"] > 0).astype(int)
z["n_noncycle"]   = z["bin"].map(lambda b: ins.get(b, {}).get("noncycle", 0))
z["ever_noncycle"]= (z["n_noncycle"] > 0).astype(int)
z["ever_inactive"]= z["bin"].map(lambda b: int(ins.get(b, {}).get("inactive", False)))
z["sample_gap_cv"]= z["bin"].map(gap_cv)
def landuse(b):
    r = pl.get(str(bin2bbl.get(b, "")).split(".")[0]) if bin2bbl.get(b) else None
    lu = (r or {}).get("landuse")
    return "residential" if lu in ("01","02","03","04","06","07","08","09","10","13","14") else "non-residential"
z["landuse_cat"] = z["bin"].map(landuse)

log("="*70); log("TIER-1 ADDITIONAL PREDICTORS — outbreak zone")
log(f"  buildings={len(z)}  cases={int(z.case.sum())}"); log("="*70)

# ---- univariate ----
log("\n--- UNIVARIATE: case vs control (median / rate), zone ---")
log(f"{'feature':<22}{'case':>10}{'control':>10}{'test':>9}{'p':>9}")
CONT = ["tower_density_200m","n_phh_viol","n_crit_viol","n_wq_viol","n_noncycle","sample_gap_cv"]
for c in CONT:
    a = z.loc[z.case==1, c].dropna(); b = z.loc[z.case==0, c].dropna()
    if len(a) < 5 or len(b) < 5: continue
    _, p = stats.mannwhitneyu(a, b)
    log(f"{c:<22}{a.median():>10.2f}{b.median():>10.2f}{'MWU':>9}{p:>9.4f}")
for c in ["ever_wq_viol","ever_noncycle","ever_inactive"]:
    ct = pd.crosstab(z[c], z.case)
    if ct.shape == (2,2):
        _, p = stats.fisher_exact(ct.values)
        log(f"{c:<22}{z.loc[z.case==1,c].mean():>10.2f}{z.loc[z.case==0,c].mean():>10.2f}{'Fisher':>9}{p:>9.4f}")
# land use
ctl = pd.crosstab(z["landuse_cat"], z.case)
log(f"\nland use (positivity): " + ", ".join(
    f"{k}={z.loc[z.landuse_cat==k,'case'].mean():.0%} (n={int((z.landuse_cat==k).sum())})"
    for k in z["landuse_cat"].unique()))

# ---- focused multivariable model: base-robust + top Tier-1 ----
for c in ["n_towers","n_samples_24mo","days_since_last_inspection"]:
    z[c] = pd.to_numeric(z[c], errors="coerce")
z["days_since_last_inspection_imp"] = z["days_since_last_inspection"].fillna(z["days_since_last_inspection"].max())
PRED = ["n_towers","n_samples_24mo","days_since_last_inspection_imp",
        "tower_density_200m","n_wq_viol","n_phh_viol"]
m = z.dropna(subset=PRED).copy()
sc = StandardScaler()
Xs = pd.DataFrame(sc.fit_transform(m[PRED]), columns=PRED, index=m.index)
X = sm.add_constant(Xs); y = m["case"].values
res = sm.Logit(y, X).fit(disp=0)
OR = np.exp(res.params); CI = np.exp(res.conf_int())
tbl = pd.DataFrame({"OR":OR,"CI_low":CI[0],"CI_high":CI[1],"p":res.pvalues}).round(3)
log(f"\n--- FOCUSED model (n={int(res.nobs)}, cases={int(m.case.sum())}, OR per 1 SD) ---")
log(tbl.to_string())
log(f"\n  McFadden R2={res.prsquared:.3f}  AUC={roc_auc_score(y,res.predict(X)):.3f}  LLR p={res.llr_pvalue:.2e}")

tbl.to_csv(REP/"odds_ratios_tier1.csv")
(REP/"stats_tier1.txt").write_text(OUT.getvalue())
z.to_csv(PROC/"analysis_table_tier1.csv", index=False)
log("\nwrote reports/stats_tier1.txt, reports/odds_ratios_tier1.csv")
