"""Build the building-level analytical table: features from cooling-tower
registration + inspection history (capped pre-outbreak), labeled case/control."""
import json, csv, re, pathlib, statistics
from datetime import date, datetime
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW, PROC = ROOT/"data"/"raw", ROOT/"data"/"processed"

REF   = date(2026, 7, 2)     # investigation start (recency reference)
CUTOFF= date(2026, 7, 1)     # exclude anything >= this (outbreak-period leakage)
OUTBREAK_ZIPS = {"10028", "10075", "10128"}

def nb(b):                    # normalize BIN ("1047674.0" -> "1047674")
    b = (b or "").strip()
    return b[:-2] if b.endswith(".0") else b
def zip5(z): return (z or "")[:5]
def to_int(x):
    try: return int(float(x))
    except: return 0
def parse_mdy(s):
    try: return datetime.strptime(s.strip(), "%m/%d/%Y").date()
    except: return None
def parse_iso(s):
    try: return datetime.fromisoformat(s.replace("Z","")).date()
    except: return None

# ---- case labels ----
case_group = {}
for r in csv.DictReader(open(PROC/"case_match_report.csv")):
    if r["matched"] == "1":
        for b in r["bins"].split(";"):
            if b: case_group[nb(b)] = r["status_group"]

# ---- registrations -> per building ----
reg = json.load(open(RAW/"registrations.json"))
bld = defaultdict(lambda: {"systems": {}, "samples": [], "reg_dates": [],
                           "zip": None, "cb": None, "nta": None,
                           "lat": [], "lon": [], "borough": None})
for r in reg:
    if r.get("borough") != "Manhattan":  # analysis universe = Manhattan
        continue
    b = nb(r.get("bin"))
    if not b: continue
    d = bld[b]
    sid = r.get("system_id")
    d["systems"][sid] = to_int(r.get("activeequipment"))
    dr = parse_iso(r.get("date_registered") or "")
    if dr: d["reg_dates"].append(dr)
    for sd in (r.get("sampledates") or "").split(","):
        pd = parse_mdy(sd)
        if pd and pd < CUTOFF:
            d["samples"].append(pd)
    d["zip"]  = d["zip"]  or zip5(r.get("zip"))
    d["cb"]   = d["cb"]   or r.get("community_board")
    d["nta"]  = d["nta"]  or r.get("ntacode")
    d["borough"] = "Manhattan"
    try: d["lat"].append(float(r["latitude"])); d["lon"].append(float(r["longitude"]))
    except: pass

# ---- inspections -> per building (pre-cutoff) ----
insp = json.load(open(RAW/"inspections.json"))
ib = defaultdict(lambda: {"dates": [], "viol": 0, "cit": 0, "vtypes": set(), "n": 0})
for r in insp:
    b = nb(r.get("bin"))
    if b not in bld: continue
    idt = parse_iso(r.get("inspection_date") or "")
    if not idt or idt >= CUTOFF: continue
    x = ib[b]; x["n"] += 1; x["dates"].append(idt)
    if (r.get("violation_code") or "").strip():
        x["viol"] += 1
        vt = (r.get("violation_type") or "").strip()
        if vt: x["vtypes"].add(vt)
    if (r.get("summons_number") or "").strip():
        x["cit"] += 1

def gaps(dates):
    ds = sorted(set(dates))
    return [ (ds[i]-ds[i-1]).days for i in range(1,len(ds)) ]

rows = []
for b, d in bld.items():
    samples = sorted(set(d["samples"]))
    g = gaps(samples)
    last_s = max(samples) if samples else None
    ins = ib.get(b, {"dates": [], "viol": 0, "cit": 0, "vtypes": set(), "n": 0})
    last_i = max(ins["dates"]) if ins["dates"] else None
    rows.append({
        "bin": b,
        "case": 1 if b in case_group else 0,
        "status_group": case_group.get(b, ""),
        "zip": d["zip"],
        "in_outbreak_zip": 1 if d["zip"] in OUTBREAK_ZIPS else 0,
        "community_board": d["cb"], "nta": d["nta"],
        "lat": round(statistics.mean(d["lat"]),6) if d["lat"] else "",
        "lon": round(statistics.mean(d["lon"]),6) if d["lon"] else "",
        # registration features
        "n_towers": len(d["systems"]),
        "n_active_towers": sum(d["systems"].values()),
        "reg_age_days": (REF - min(d["reg_dates"])).days if d["reg_dates"] else "",
        # sampling history
        "n_samples": len(samples),
        "never_sampled": 1 if not samples else 0,
        "days_since_last_sample": (REF - last_s).days if last_s else "",
        "n_samples_12mo": sum(1 for s in samples if (REF-s).days <= 365),
        "n_samples_24mo": sum(1 for s in samples if (REF-s).days <= 730),
        "median_gap_days": round(statistics.median(g),1) if g else "",
        "max_gap_days": max(g) if g else "",
        "overdue_90d": 1 if (last_s and (REF-last_s).days > 90) or (not last_s) else 0,
        # inspection history
        "n_inspections": ins["n"],
        "n_violations": ins["viol"],
        "n_citations": ins["cit"],
        "ever_violation": 1 if ins["viol"] > 0 else 0,
        "n_violation_types": len(ins["vtypes"]),
        "days_since_last_inspection": (REF - last_i).days if last_i else "",
    })

cols = list(rows[0].keys())
with open(PROC/"analysis_table.csv","w",newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)

n=len(rows); ncase=sum(r["case"] for r in rows)
zone=[r for r in rows if r["in_outbreak_zip"]]
print(f"buildings (Manhattan): {n}  cases: {ncase}")
print(f"outbreak-zip buildings: {len(zone)}  cases in zone: {sum(r['case'] for r in zone)}")
print(f"cases outside outbreak zips: {ncase - sum(r['case'] for r in zone)}")
print("wrote data/processed/analysis_table.csv  cols:", len(cols))
