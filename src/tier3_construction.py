"""Tier-3 (long shot): does proximity to active major construction predict tower
positivity? Construction can aerosolize dust/soil and disturb water systems.
Distance from each outbreak-zone building to the nearest recent major DOB permit."""
import json, math, urllib.parse, urllib.request, pathlib, io
import numpy as np, pandas as pd
from scipy import stats
ROOT=pathlib.Path(__file__).resolve().parent.parent
RAW,PROC,REP=ROOT/"data"/"raw",ROOT/"data"/"processed",ROOT/"reports"
def soda(ds,p):
    u=f"https://data.cityofnewyork.us/resource/{ds}.json?"+urllib.parse.urlencode(p)
    r=urllib.request.Request(u,headers={"User-Agent":"cooling-data-analysis"})
    with urllib.request.urlopen(r,timeout=120) as x: return json.load(x)
def num(x):
    try:
        v=float(x); return v if math.isfinite(v) else None
    except: return None
def meters(la1,lo1,la2,lo2):
    R=6371000.0;m=math.radians
    x=(m(lo2)-m(lo1))*math.cos(m((la1+la2)/2));y=m(la2)-m(la1)
    return R*math.hypot(x,y)

# current DOB NOW construction/renovation permits in the UES bounding box
rows=[]; off=0
while True:
    ch=soda("rbx6-tga4",{"$select":"latitude,longitude,work_type,permit_status",
        "$where":"latitude between 40.766 and 40.792 AND longitude between -73.968 and -73.940",
        "$limit":50000,"$offset":off,"$order":":id"})
    rows+=ch
    if len(ch)<50000: break
    off+=50000
sites=[]
for r in rows:
    la,lo=num(r.get("latitude")),num(r.get("longitude"))
    if la and lo: sites.append((la,lo))
json.dump(sites,open(RAW/"construction_ues.json","w"))
OUT=io.StringIO()
def log(*a): print(*a);print(*a,file=OUT)
log(f"Manhattan major permits since 2024-07: {len(rows)}; within UES bbox: {len(sites)}")

base=pd.read_csv(PROC/"analysis_table.csv"); base["bin"]=base["bin"].astype(str)
z=base[base.in_outbreak_zip==1].dropna(subset=["lat","lon"]).copy()
def nearest(la,lo):
    if not sites: return np.nan
    return min(meters(la,lo,s[0],s[1]) for s in sites)
def within(la,lo,r=150):
    return sum(1 for s in sites if meters(la,lo,s[0],s[1])<=r)
z["dist_construction_m"]=[nearest(r.lat,r.lon) for r in z.itertuples()]
z["n_construction_150m"]=[within(r.lat,r.lon) for r in z.itertuples()]

log(f"\nzone buildings={len(z)} cases={int(z.case.sum())}")
log("\n--- construction proximity: case vs control ---")
for c in ["dist_construction_m","n_construction_150m"]:
    a=z.loc[z.case==1,c].dropna(); b=z.loc[z.case==0,c].dropna()
    _,p=stats.mannwhitneyu(a,b)
    log(f"  {c:<22} case_med={a.median():>8.1f}  control_med={b.median():>8.1f}  p={p:.4f}")
(REP/"stats_tier3.txt").write_text(OUT.getvalue())
z[["bin","case","dist_construction_m","n_construction_150m"]].to_csv(PROC/"tier3_construction.csv",index=False)
log("\nwrote reports/stats_tier3.txt")
