"""#1/#2 Relational: do the 76 positive buildings cluster under shared owners,
managing entities, or contractors? Join PLUTO ownername + DOB NOW permit
owner/applicant (contractor) business names by BBL to the outbreak zone."""
import json, urllib.parse, urllib.request, pathlib, io, re
import numpy as np, pandas as pd
from collections import Counter, defaultdict
from scipy import stats
ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW, PROC, REP = ROOT/"data"/"raw", ROOT/"data"/"processed", ROOT/"reports"
def soda(ds, p):
    u = f"https://data.cityofnewyork.us/resource/{ds}.json?"+urllib.parse.urlencode(p)
    r = urllib.request.Request(u, headers={"User-Agent": "cooling-data-analysis"})
    with urllib.request.urlopen(r, timeout=120) as x: return json.load(x)
def chunks(xs, n):
    for i in range(0, len(xs), n): yield xs[i:i+n]
def norm_name(s):
    s = (s or "").upper().strip()
    s = re.sub(r"[.,]", " ", s)
    s = re.sub(r"\b(LLC|L L C|INC|CORP|CO|LP|LLP|LTD|COMPANY|ASSOCIATES|ASSOC|"
               r"REALTY|MANAGEMENT|MGMT|PROPERTIES|OWNER|HOLDINGS|GROUP|THE)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()

bin2bbl = {k: str(v).split(".")[0] for k, v in json.load(open(PROC/"bin2bbl_zone.json")).items()}
bbls = sorted(set(bin2bbl.values()))
OUT = io.StringIO()
def log(*a): print(*a); print(*a, file=OUT)

# ---- PLUTO ownername by BBL ----
owner = {}
for c in chunks(bbls, 70):
    inlist = ",".join(f"'{b}'" for b in c)
    for r in soda("64uk-42ks", {"$select": "bbl,ownername",
                  "$where": f"bbl in({inlist})", "$limit": 5000}):
        owner[str(r["bbl"]).split(".")[0]] = r.get("ownername")

# ---- DOB NOW permits by BBL: owner + applicant (contractor) business ----
permit_owner, permit_contractor = defaultdict(set), defaultdict(set)
for c in chunks(bbls, 70):
    inlist = ",".join(f"'{b}'" for b in c)
    for r in soda("rbx6-tga4", {"$select": "bbl,owner_business_name,applicant_business_name",
                  "$where": f"bbl in({inlist})", "$limit": 50000}):
        b = str(r.get("bbl", "")).split(".")[0]
        if r.get("owner_business_name"): permit_owner[b].add(norm_name(r["owner_business_name"]))
        if r.get("applicant_business_name"): permit_contractor[b].add(norm_name(r["applicant_business_name"]))

base = pd.read_csv(PROC/"analysis_table.csv"); base["bin"] = base["bin"].astype(str)
z = base[base.in_outbreak_zip == 1].copy()
z["bbl"] = z["bin"].map(bin2bbl)
z["owner"] = z["bbl"].map(lambda b: norm_name(owner.get(b, "")))
z["contractors"] = z["bbl"].map(lambda b: permit_contractor.get(b, set()))

log("="*66); log("#1/#2  SHARED OWNER / CONTRACTOR NETWORK — outbreak zone")
log(f"  buildings={len(z)} cases={int(z.case.sum())}"); log("="*66)

# --- owners repeated across buildings ---
def repeat_stats(label, series_map):
    # series_map: bin -> set(names); count buildings sharing >=1 name with another building
    name_bldgs = defaultdict(set)
    for b, names in series_map.items():
        for nm in names:
            if nm: name_bldgs[nm].add(b)
    shared = {b: any(len(name_bldgs[nm]) > 1 for nm in names if nm) for b, names in series_map.items()}
    # among positives vs controls: share a name with ANOTHER POSITIVE?
    pos = set(z.loc[z.case==1, "bin"]); ctl = set(z.loc[z.case==0, "bin"])
    def shares_with_pos(b, names):
        return any(len((name_bldgs[nm] & pos) - {b}) > 0 for nm in names if nm)
    pos_share = np.mean([shares_with_pos(b, series_map.get(b, set())) for b in pos])
    ctl_share = np.mean([shares_with_pos(b, series_map.get(b, set())) for b in ctl])
    log(f"\n{label}: shares an entity with another POSITIVE building")
    log(f"   positives: {pos_share:.0%}   controls: {ctl_share:.0%}")
    # names most over-represented among positives
    over = []
    for nm, bs in name_bldgs.items():
        if len(bs) >= 2:
            np_ = len(bs & pos); nc_ = len(bs & ctl)
            if np_ >= 2: over.append((nm, np_, nc_))
    over.sort(key=lambda t: -t[1])
    if over:
        log(f"   entities on >=2 positive buildings:")
        for nm, npv, ncv in over[:10]:
            log(f"     {nm[:40]:<42} positives={npv} controls={ncv}")
    else:
        log("   (no entity appears on >=2 positive buildings)")

# owner as single-name sets
repeat_stats("PLUTO owner name", {b: {z.loc[z.bin==b,'owner'].iloc[0]} for b in z.bin})
repeat_stats("DOB permit contractor", {r.bin: r.contractors for r in z.itertuples()})

log("\nNote: NYC buildings are typically each held by a distinct single-asset LLC,")
log("so PLUTO owner rarely repeats; contractors/managing agents are the real test.")
(REP/"stats_tier4_network.txt").write_text(OUT.getvalue())
log("\nwrote reports/stats_tier4_network.txt")
