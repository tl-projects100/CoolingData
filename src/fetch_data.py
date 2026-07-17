"""Fetch NYC cooling-tower datasets from Socrata (NYC Open Data)."""
import os, sys, json, time, pathlib, urllib.parse, urllib.request

RAW = pathlib.Path(__file__).resolve().parent.parent / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
BASE = "https://data.cityofnewyork.us/resource/{}.json"
DATASETS = {"registrations": "y4fw-iqfr", "inspections": "f9wb-g8mb"}

def fetch(dsid, where=None, page=50000):
    # NOTE: datasets are public; the supplied app token was rejected (403), so
    # we fetch unauthenticated. Our pull is only a few requests, well within limits.
    out, off = [], 0
    while True:
        params = {"$limit": page, "$offset": off, "$order": ":id"}
        if where: params["$where"] = where
        url = BASE.format(dsid) + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={
              "User-Agent": "Mozilla/5.0 cooling-data-analysis"})
        with urllib.request.urlopen(req, timeout=120) as r:
            chunk = json.load(r)
        out.extend(chunk)
        if len(chunk) < page: break
        off += page
        time.sleep(0.2)
    return out

if __name__ == "__main__":
    for name, dsid in DATASETS.items():
        rows = fetch(dsid)
        (RAW / f"{name}.json").write_text(json.dumps(rows))
        print(f"{name} ({dsid}): {len(rows)} rows -> data/raw/{name}.json", flush=True)

    # UES street-grid basemap (NYC Street Centerline / CSCL) for the map artifact
    box = "40.7895,-73.9665,40.7690,-73.9420"   # N,W,S,E covering the outbreak ZIPs
    q = urllib.parse.urlencode({"$where": f"within_box(the_geom,{box})", "$limit": 8000,
                                "$select": "the_geom,street_name,stname_label"})
    url = f"https://data.cityofnewyork.us/resource/inkn-q76z.geojson?{q}"
    req = urllib.request.Request(url, headers={"User-Agent": "cooling-data-analysis"})
    with urllib.request.urlopen(req, timeout=120) as r:
        gj = r.read()
    (RAW / "ues_streets.geojson").write_bytes(gj)
    print(f"ues_streets (inkn-q76z): -> data/raw/ues_streets.geojson", flush=True)
