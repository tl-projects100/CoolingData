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
