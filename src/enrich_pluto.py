"""Enrich the outbreak-zone table with PLUTO building attributes (by BBL) and
re-run the logistic model as a sensitivity analysis: do building age / size
explain the registration-age and sampling-frequency signals?"""
import json, urllib.parse, urllib.request, pathlib, io
import numpy as np, pandas as pd
import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
import warnings; warnings.filterwarnings("ignore")

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW, PROC, REP = ROOT/"data"/"raw", ROOT/"data"/"processed", ROOT/"reports"
PLUTO = "64uk-42ks"
COLS = ["bbl","yearbuilt","numfloors","unitsres","unitstotal","bldgarea",
        "assesstot","landuse","bldgclass"]

def fetch_pluto(bbls):
    out = []
    bbls = list(bbls)
    for i in range(0, len(bbls), 80):
        chunk = bbls[i:i+80]
        inlist = ",".join(f"'{b}'" for b in chunk)
        params = {"$select": ",".join(COLS), "$where": f"bbl in({inlist})", "$limit": 5000}
        url = f"https://data.cityofnewyork.us/resource/{PLUTO}.json?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": "cooling-data-analysis"})
        with urllib.request.urlopen(req, timeout=120) as r:
            out.extend(json.load(r))
    return out

bin2bbl = json.load(open(PROC/"bin2bbl_zone.json"))
pl = fetch_pluto(set(bin2bbl.values()))
json.dump(pl, open(RAW/"pluto_zone.json", "w"))
plu = {str(r["bbl"]).split(".")[0]: r for r in pl}
print(f"PLUTO rows fetched: {len(pl)}  unique BBL: {len(plu)}")

df = pd.read_csv(PROC/"analysis_table.csv")
z = df[df.in_outbreak_zip == 1].copy()
z["bin"] = z["bin"].astype(str)
z["bbl"] = z["bin"].map(bin2bbl)
def g(bbl, k):
    r = plu.get(str(bbl));
    if not r: return np.nan
    try: return float(r.get(k))
    except: return np.nan
for k in ["yearbuilt","numfloors","unitsres","unitstotal","bldgarea","assesstot"]:
    z[k] = z["bbl"].map(lambda b: g(b, k))
z["landuse"] = z["bbl"].map(lambda b: (plu.get(str(b)) or {}).get("landuse"))
z.loc[z["yearbuilt"].fillna(0) < 1800, "yearbuilt"] = np.nan
z["bldg_age_yrs"] = 2026 - z["yearbuilt"]
z["log_assess"] = np.log10(z["assesstot"].where(z["assesstot"] > 0))

cov = z.dropna(subset=["yearbuilt"])
OUT = io.StringIO()
def log(*a): print(*a); print(*a, file=OUT)

log("="*70); log("PLUTO ENRICHMENT — outbreak zone")
log("="*70)
log(f"buildings with PLUTO match: {z['yearbuilt'].notna().sum()}/{len(z)}")
log("\n--- building attributes: case vs control (median) ---")
from scipy import stats
for c in ["bldg_age_yrs","numfloors","unitsres","unitstotal","bldgarea","assesstot"]:
    a = z.loc[z.case==1, c].dropna(); b = z.loc[z.case==0, c].dropna()
    if len(a) < 5 or len(b) < 5: continue
    _, p = stats.mannwhitneyu(a, b)
    log(f"  {c:<14} case={a.median():>12.0f}  control={b.median():>12.0f}  p={p:.3f}")

# --- enriched multivariable model ---
for c in ["reg_age_days","n_samples_24mo","n_violations","days_since_last_inspection","n_towers"]:
    z[c] = pd.to_numeric(z[c], errors="coerce")
z["reg_age_yrs"] = z["reg_age_days"]/365.25
z["days_since_last_inspection_imp"] = z["days_since_last_inspection"].fillna(z["days_since_last_inspection"].max())
PRED = ["n_towers","reg_age_yrs","n_samples_24mo","n_violations",
        "days_since_last_inspection_imp","bldg_age_yrs","numfloors","unitsres","log_assess"]
m = z.dropna(subset=PRED).copy()
sc = StandardScaler()
Xs = pd.DataFrame(sc.fit_transform(m[PRED]), columns=PRED, index=m.index)
X = sm.add_constant(Xs); y = m["case"].values
res = sm.Logit(y, X).fit(disp=0)
OR = np.exp(res.params); CI = np.exp(res.conf_int())
tbl = pd.DataFrame({"OR":OR,"CI_low":CI[0],"CI_high":CI[1],"p":res.pvalues}).round(3)
log(f"\n--- ENRICHED logistic (n={int(res.nobs)}, cases={int(m.case.sum())}, "
    f"OR per 1 SD) ---")
log(tbl.to_string())
log(f"\n  McFadden R2={res.prsquared:.3f}  AUC={roc_auc_score(y,res.predict(X)):.3f}  "
    f"LLR p={res.llr_pvalue:.2e}")
tbl.to_csv(REP/"odds_ratios_pluto.csv")
(REP/"stats_pluto.txt").write_text(OUT.getvalue())
z.to_csv(PROC/"analysis_table_pluto.csv", index=False)
log("\nwrote reports/stats_pluto.txt, reports/odds_ratios_pluto.csv")
