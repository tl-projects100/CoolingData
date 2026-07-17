"""Match the 76 case buildings to registered cooling towers and build a
building-level labeled table (case=1 / control=0) for Manhattan."""
import json, csv, re, pathlib
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW, PROC = ROOT/"data"/"raw", ROOT/"data"/"processed"
PROC.mkdir(parents=True, exist_ok=True)

WORDNUM = {"first":"1","second":"2","third":"3","fourth":"4","fifth":"5",
           "sixth":"6","seventh":"7","eighth":"8","ninth":"9","tenth":"10",
           "eleventh":"11","twelfth":"12"}
SUFFIX = {"street":"st","st":"st","avenue":"ave","ave":"ave","av":"ave",
          "place":"pl","pl":"pl","boulevard":"blvd","blvd":"blvd","road":"rd",
          "rd":"rd","drive":"dr","dr":"dr","lane":"ln","terrace":"ter","court":"ct"}

def norm_street(s):
    s = s.lower().replace(".", " ")
    s = re.sub(r"\s+", " ", s).strip()
    toks = []
    for t in s.split():
        t = re.sub(r"^(\d+)(st|nd|rd|th)$", r"\1", t)   # 82nd -> 82
        t = WORDNUM.get(t, t)                            # fifth -> 5
        if t in ("east",): t = "e"
        elif t in ("west",): t = "w"
        elif t in ("north",): t = "n"
        elif t in ("south",): t = "s"
        t = SUFFIX.get(t, t)                             # street -> st
        toks.append(t)
    return " ".join(toks)

def norm_addr(raw):
    m = re.match(r"\s*(\d+)\s+(.*)$", raw)
    if not m: return None, None
    return m.group(1), norm_street(m.group(2))

# --- index registrations by (number, street_key), Manhattan only ---
reg = json.load(open(RAW/"registrations.json"))
by_key = defaultdict(list)
for r in reg:
    if r.get("borough") != "Manhattan": continue
    num = (r.get("number") or "").strip()
    key = (num, norm_street(r.get("street") or ""))
    by_key[key].append(r)

# --- match cases ---
cases = list(csv.DictReader(open(RAW/"affected_buildings.csv")))
matched, unmatched = [], []
case_bins = {}   # bin -> status_group
for c in cases:
    num, skey = norm_addr(c["address_raw"])
    hits = by_key.get((num, skey), [])
    if hits:
        bins = sorted(set(h["bin"] for h in hits))
        matched.append((c["address_raw"], c["status_group"], num, skey, bins, len(hits)))
        for h in hits: case_bins[h["bin"]] = c["status_group"]
    else:
        unmatched.append((c["address_raw"], c["status_group"], num, skey))

print(f"=== MATCHED {len(matched)}/{len(cases)} case buildings ===")
for a,g,n,s,bins,k in matched:
    print(f"  OK  {a:28s} -> {n} {s:16s} bins={bins} towers={k}")
print(f"\n=== UNMATCHED {len(unmatched)} ===")
for a,g,n,s in unmatched:
    print(f"  ??  {a:28s} -> norm=({n!r},{s!r})  group={g}")

# save intermediate match report
with open(PROC/"case_match_report.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["address_raw","status_group","num","street_key","bins","n_towers","matched"])
    for a,g,n,s,bins,k in matched: w.writerow([a,g,n,s,";".join(bins),k,1])
    for a,g,n,s in unmatched: w.writerow([a,g,n,s,"",0,0])
print(f"\nunique matched BINs: {len(set(b for _,_,_,_,bins,_ in matched for b in bins))}")
