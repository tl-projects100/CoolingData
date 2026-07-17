"""#9-design: join NYS Cooling Tower Registry (gd58-9fej) tower HARDWARE
attributes — manufacturer, model, cooling capacity, intended use — to the
outbreak-zone buildings by address, and test against positivity. These are the
tower-design variables absent from the NYC datasets."""
import json, urllib.parse, urllib.request, pathlib, io, re
import numpy as np, pandas as pd
from collections import defaultdict
from scipy import stats
ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW, PROC, REP = ROOT/"data"/"raw", ROOT/"data"/"processed", ROOT/"reports"

def soda(host, ds, p):
    u = f"https://{host}/resource/{ds}.json?"+urllib.parse.urlencode(p)
    r = urllib.request.Request(u, headers={"User-Agent": "cooling-data-analysis"})
    with urllib.request.urlopen(r, timeout=120) as x: return json.load(x)
WORDNUM = {"first":"1","second":"2","third":"3","fourth":"4","fifth":"5","sixth":"6",
           "seventh":"7","eighth":"8","ninth":"9","tenth":"10"}
SUF = {"street":"st","st":"st","avenue":"ave","ave":"ave","av":"ave","place":"pl","pl":"pl"}
def norm_street(s):
    s = (s or "").lower().replace(".", " "); toks = []
    for t in re.sub(r"\s+", " ", s).strip().split():
        t = re.sub(r"^(\d+)(st|nd|rd|th)$", r"\1", t); t = WORDNUM.get(t, t)
        t = {"east":"e","west":"w","north":"n","south":"s"}.get(t, t); t = SUF.get(t, t)
        toks.append(t)
    return " ".join(toks)

# ---- fetch NYS registry for New York county (Manhattan) ----
nys, off = [], 0
while True:
    ch = soda("health.data.ny.gov", "gd58-9fej", {
        "$select": "location_number,location_street_name,location_county,manufacturer,"
                   "model_number,cooling_capacity,intended_use",
        "$where": "location_county='New York'", "$limit": 50000, "$offset": off, "$order": ":id"})
    nys += ch
    if len(ch) < 50000: break
    off += 50000
json.dump(nys, open(RAW/"nys_registry_ny.json", "w"))
OUT = io.StringIO(); log = lambda *a: (print(*a), print(*a, file=OUT))
log(f"NYS registry rows (New York county): {len(nys)}")

def numcap(x):
    try: return float(x)
    except: return np.nan
by_addr = defaultdict(lambda: {"mfr": set(), "model": set(), "cap": [], "use": set()})
for r in nys:
    key = (str(r.get("location_number","")).strip(), norm_street(r.get("location_street_name")))
    d = by_addr[key]
    if r.get("manufacturer"): d["mfr"].add(r["manufacturer"].upper().strip())
    if r.get("model_number"): d["model"].add(r["model_number"].upper().strip())
    c = numcap(r.get("cooling_capacity"));
    if not np.isnan(c): d["cap"].append(c)
    if r.get("intended_use"): d["use"].add(r["intended_use"].upper().strip())

# ---- zone building -> (number, street_key) from registrations ----
reg = json.load(open(RAW/"registrations.json"))
def nb(b): b=(b or "").strip(); return b[:-2] if b.endswith(".0") else b
bin_addr = {}
for r in reg:
    if r.get("borough") != "Manhattan": continue
    b = nb(r.get("bin"))
    bin_addr.setdefault(b, (str(r.get("number","")).strip(), norm_street(r.get("street"))))

base = pd.read_csv(PROC/"analysis_table.csv"); base["bin"] = base["bin"].astype(str)
z = base[base.in_outbreak_zip == 1].copy()
def feat(b, kind):
    d = by_addr.get(bin_addr.get(b, ("", "")))
    if not d: return np.nan
    if kind == "n_mfr": return len(d["mfr"])
    if kind == "n_model": return len(d["model"])
    if kind == "max_cap": return max(d["cap"]) if d["cap"] else np.nan
    if kind == "sum_cap": return sum(d["cap"]) if d["cap"] else np.nan
    if kind == "matched": return 1
    return np.nan
z["nys_matched"]   = z["bin"].map(lambda b: 1 if by_addr.get(bin_addr.get(b, ("",""))) else 0)
z["tower_max_cap"] = z["bin"].map(lambda b: feat(b, "max_cap"))
z["tower_sum_cap"] = z["bin"].map(lambda b: feat(b, "sum_cap"))
z["n_manufacturers"] = z["bin"].map(lambda b: feat(b, "n_mfr"))

log(f"zone buildings matched to NYS registry: {int(z['nys_matched'].sum())}/{len(z)}")
log("\n--- tower-hardware attributes: case vs control (median) ---")
for c in ["tower_max_cap","tower_sum_cap","n_manufacturers"]:
    a = z.loc[z.case==1, c].dropna(); b = z.loc[z.case==0, c].dropna()
    if len(a) < 5 or len(b) < 5:
        log(f"  {c:<18} too few matches"); continue
    _, p = stats.mannwhitneyu(a, b)
    log(f"  {c:<18} case={a.median():>10.1f}  control={b.median():>10.1f}  n={len(a)+len(b)}  p={p:.4f}")

# top manufacturers among positives vs controls
mfr_pos, mfr_ctl = defaultdict(int), defaultdict(int)
for r in z.itertuples():
    d = by_addr.get(bin_addr.get(r.bin, ("","")))
    if not d: continue
    for m in d["mfr"]:
        (mfr_pos if r.case==1 else mfr_ctl)[m] += 1
log("\n--- top tower manufacturers (positives vs controls) ---")
for m in sorted(set(mfr_pos)|set(mfr_ctl), key=lambda k:-(mfr_pos[k]+mfr_ctl[k]))[:10]:
    log(f"   {m[:30]:<32} positives={mfr_pos[m]:>3}  controls={mfr_ctl[m]:>3}")
(REP/"stats_tier4_design.txt").write_text(OUT.getvalue())
log("\nwrote reports/stats_tier4_design.txt")
