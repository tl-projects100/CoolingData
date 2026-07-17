"""Tier-2 predictors: LL84 energy/water benchmarking (cooling-load / tower
makeup-water proxy) + DOB and HPD violations (building-management quality,
independent of the tower-specific inspections). Joined by BBL to the outbreak
zone; univariate + focused logistic model with a multiple-comparison caveat.
"""
import json, urllib.parse, urllib.request, pathlib, io
import numpy as np, pandas as pd
from scipy import stats
import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
import warnings; warnings.filterwarnings("ignore")

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW, PROC, REP = ROOT/"data"/"raw", ROOT/"data"/"processed", ROOT/"reports"
OUT = io.StringIO()
def log(*a): print(*a); print(*a, file=OUT)

def soda(ds, params):
    url = f"https://data.cityofnewyork.us/resource/{ds}.json?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "cooling-data-analysis"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)
def chunks(xs, n):
    for i in range(0, len(xs), n): yield xs[i:i+n]
def num(x):
    try:
        v = float(x)
        return v if np.isfinite(v) else np.nan
    except: return np.nan

zb = json.load(open(PROC/"_zone_bbls.json"))
bbls, blocks = zb["bbls"], zb["blocks"]
bin2bbl = {k: str(v).split(".")[0] for k, v in json.load(open(PROC/"bin2bbl_zone.json")).items()}

# ---------- LL84: latest-year, main (max-GFA) row per BBL ----------
ll = []
for c in chunks(bbls, 60):
    inlist = ",".join(f"'{b}'" for b in c)
    ll += soda("5zyy-y8am", {"$where": f"nyc_borough_block_and_lot in({inlist})",
        "$select": "nyc_borough_block_and_lot,report_year,site_eui_kbtu_ft,source_eui_kbtu_ft,"
                   "weather_normalized_site_eui,water_use_all_water_sources,"
                   "property_gfa_calculated,energy_star_score", "$limit": 50000})
json.dump(ll, open(RAW/"ll84_zone.json", "w"))
best = {}
for r in ll:
    b = str(r.get("nyc_borough_block_and_lot", "")).split(".")[0]
    yr = num(r.get("report_year")); gfa = num(r.get("property_gfa_calculated"))
    key = (num(r.get("site_eui_kbtu_ft")) is not np.nan)
    cur = best.get(b)
    score = (yr if np.isfinite(yr) else 0, gfa if np.isfinite(gfa) else 0)
    if cur is None or score > cur[0]:
        best[b] = (score, r)
def ll_feat(bbl, k):
    r = best.get(bbl); return num(r[1].get(k)) if r else np.nan
log(f"LL84: {len(ll)} rows -> {len(best)}/{len(bbls)} BBLs with a benchmarking record")

# ---------- DOB violations: grouped counts per lot (pre-cutoff) ----------
def grouped(ds, extra_where, boro_field, extra_select="", date_field=None):
    rows = []
    for c in chunks(blocks, 40):
        inlist = ",".join(f"'{b}'" for b in c)
        w = f"{boro_field}='1' AND block in({inlist})"
        if extra_where: w += f" AND {extra_where}"
        rows += soda(ds, {"$select": f"block,lot,count(1) as n{extra_select}",
            "$where": w, "$group": "block,lot", "$limit": 50000})
    return rows
def bbl_of(block, lot):
    try:
        return "1" + str(block).strip().replace(" ", "").zfill(5) + \
               str(int(float(str(lot).strip().replace(" ", "")))).zfill(4)
    except (ValueError, TypeError):
        return None

dob = grouped("3h2n-5cm9", "issue_date < '20260701'", "boro")
dob_n = {}
for r in dob:
    b = bbl_of(r["block"], r["lot"])
    if b: dob_n[b] = dob_n.get(b, 0) + (num(r["n"]) if np.isfinite(num(r["n"])) else 0)
json.dump(dob, open(RAW/"dob_zone.json", "w"))
log(f"DOB: {len(dob)} lot-groups; matched BBLs {sum(1 for b in bbls if b in dob_n)}")

# ---------- HPD violations: grouped counts + class C (pre-cutoff) ----------
hpd = []
for c in chunks(blocks, 40):
    inlist = ",".join(f"'{b}'" for b in c)
    hpd += soda("wvxf-dwi5", {"$select": "block,lot,class,count(1) as n",
        "$where": f"boroid='1' AND block in({inlist}) AND novissueddate < '2026-07-01'",
        "$group": "block,lot,class", "$limit": 50000})
json.dump(hpd, open(RAW/"hpd_zone.json", "w"))
hpd_n, hpd_c = {}, {}
for r in hpd:
    b = bbl_of(r["block"], r["lot"]); n = num(r["n"])
    if not b: continue
    hpd_n[b] = hpd_n.get(b, 0) + (n if np.isfinite(n) else 0)
    if (r.get("class") or "").upper() == "C":
        hpd_c[b] = hpd_c.get(b, 0) + (n if np.isfinite(n) else 0)
log(f"HPD: {len(hpd)} class-groups; matched BBLs {sum(1 for b in bbls if b in hpd_n)}")

# ---------- assemble zone table ----------
base = pd.read_csv(PROC/"analysis_table.csv"); base["bin"] = base["bin"].astype(str)
z = base[base.in_outbreak_zip == 1].copy()
z["bbl"] = z["bin"].map(bin2bbl)
z["site_eui"]        = z["bbl"].map(lambda b: ll_feat(b, "site_eui_kbtu_ft"))
z["water_use_kgal"]  = z["bbl"].map(lambda b: ll_feat(b, "water_use_all_water_sources"))
z["gfa"]             = z["bbl"].map(lambda b: ll_feat(b, "property_gfa_calculated"))
z["energy_star"]     = z["bbl"].map(lambda b: ll_feat(b, "energy_star_score"))
z["water_intensity"] = z["water_use_kgal"] / z["gfa"]     # kgal per sq ft
z["n_dob_viol"]      = z["bbl"].map(lambda b: dob_n.get(b, 0))
z["n_hpd_viol"]      = z["bbl"].map(lambda b: hpd_n.get(b, 0))
z["n_hpd_classC"]    = z["bbl"].map(lambda b: hpd_c.get(b, 0))

log("\n" + "="*66); log("TIER-2 PREDICTORS — outbreak zone (LL84 + DOB + HPD)")
log(f"  buildings={len(z)}  cases={int(z.case.sum())}"); log("="*66)
log("\n--- UNIVARIATE: case vs control (median), zone ---")
log(f"{'feature':<20}{'case':>12}{'control':>12}{'n':>7}{'p':>9}")
CONT = ["site_eui","water_use_kgal","water_intensity","energy_star",
        "n_dob_viol","n_hpd_viol","n_hpd_classC"]
for c in CONT:
    a = z.loc[z.case==1, c].dropna(); b = z.loc[z.case==0, c].dropna()
    if len(a) < 5 or len(b) < 5:
        log(f"{c:<20}{'(too few non-missing)':>40}"); continue
    _, p = stats.mannwhitneyu(a, b)
    log(f"{c:<20}{a.median():>12.2f}{b.median():>12.2f}{len(a)+len(b):>7}{p:>9.4f}")

# ---------- focused model: robust base + Tier-2 ----------
for c in ["n_towers","n_samples_24mo","days_since_last_inspection"]:
    z[c] = pd.to_numeric(z[c], errors="coerce")
z["days_since_last_inspection_imp"] = z["days_since_last_inspection"].fillna(z["days_since_last_inspection"].max())
z["log_water"] = np.log10(z["water_use_kgal"].where(z["water_use_kgal"] > 0))
PRED = ["n_towers","n_samples_24mo","days_since_last_inspection_imp",
        "site_eui","log_water","n_dob_viol"]
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
tbl.to_csv(REP/"odds_ratios_tier2.csv")
(REP/"stats_tier2.txt").write_text(OUT.getvalue())
z.to_csv(PROC/"analysis_table_tier2.csv", index=False)
log("\nwrote reports/stats_tier2.txt, reports/odds_ratios_tier2.csv")
