"""Build reports/map_data.json for the map artifacts. Uses PLUTO tax-lot
centroids (a point inside the building's lot) instead of the registration
address-geocode, so dots land on buildings rather than the street."""
import json, urllib.parse, urllib.request, pathlib
import pandas as pd
ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW, PROC = ROOT/"data"/"raw", ROOT/"data"/"processed"
def soda(ds, p):
    u = f"https://data.cityofnewyork.us/resource/{ds}.json?"+urllib.parse.urlencode(p)
    r = urllib.request.Request(u, headers={"User-Agent": "cooling-data-analysis"})
    with urllib.request.urlopen(r, timeout=120) as x: return json.load(x)

bin2bbl = {k: str(v).split(".")[0] for k, v in json.load(open(PROC/"bin2bbl_zone.json")).items()}
bbls = sorted(set(bin2bbl.values()))
coords = {}
for i in range(0, len(bbls), 70):
    inlist = ",".join(f"'{b}'" for b in bbls[i:i+70])
    for r in soda("64uk-42ks", {"$select": "bbl,latitude,longitude",
                  "$where": f"bbl in({inlist})", "$limit": 5000}):
        try: coords[str(r["bbl"]).split(".")[0]] = (float(r.get("latitude")), float(r.get("longitude")))
        except (TypeError, ValueError): pass
json.dump(coords, open(RAW/"pluto_coords_zone.json", "w"))

reg = json.load(open(RAW/"registrations.json"))
def nb(b): b=(b or "").strip(); return b[:-2] if b.endswith(".0") else b
addr = {}
for r in reg:
    b = nb(r.get("bin"))
    if b and b not in addr:
        addr[b] = f"{(r.get('number') or '').strip()} {(r.get('street') or '').strip().title()}".strip()

df = pd.read_csv(PROC/"analysis_table.csv"); df["bin"] = df["bin"].astype(str)
z = df[df.in_outbreak_zip == 1].copy()
pts, moved = [], 0
for r in z.itertuples():
    bbl = bin2bbl.get(r.bin); c = coords.get(bbl)
    lat, lon = (c if c else (r.lat, r.lon))
    if c: moved += 1
    if pd.isna(lat) or pd.isna(lon): continue
    pts.append({"a": addr.get(r.bin, r.bin), "lat": round(float(lat),6), "lon": round(float(lon),6),
                "c": int(r.case), "zip": str(r.zip).split(".")[0], "nt": int(r.n_towers),
                "age": None if pd.isna(r.reg_age_days) else round(r.reg_age_days/365.25,1),
                "dls": None if pd.isna(pd.to_numeric(r.days_since_last_sample, errors="coerce"))
                       else int(pd.to_numeric(r.days_since_last_sample, errors="coerce")),
                "nv": int(r.n_violations)})
out = {"meta": {"n": len(pts), "cases": sum(p["c"] for p in pts),
       "controls": sum(1 for p in pts if p["c"]==0), "coord_source": "PLUTO lot centroid"}, "points": pts}
json.dump(out, open(ROOT/"reports"/"map_data.json", "w"))
print(f"map_data.json: {len(pts)} pts; {moved} on PLUTO centroid, {len(pts)-moved} fallback")
