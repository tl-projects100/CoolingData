"""Assemble the canonical case list of buildings ordered to clean/disinfect
cooling towers in the 2026 UES Legionnaires' cluster.

Sources:
  - DOH preliminary press release (2026-07-10): 31 buildings (2 status groups),
    scraped from the page's list markup.
  - DOH update (buildings added after 07-10), provided as text: 45 buildings
    (2 registered status groups + 1 unregistered).
Total = 76 buildings.
"""
import csv, re, pathlib

RAW = pathlib.Path(__file__).resolve().parent.parent / "data" / "raw"

# --- Group A: DOH 07-10, remediation complete (19) ---
A = """180 East End Ave.;1750 York Ave.;1660 Second Ave;1438 Third Ave.;1511 Third Ave.;
1551 Third Ave.;1071 Fifth Ave.;1080 Fifth Ave.;1001 Fifth Ave.;240 E. 82nd St.;8 E. 83rd St.;
145 E. 84th St.;117 E. 85th St.;125 E. 87th St.;152 E. 87th St.;120 E. 87th St.;501 E. 87th St.;
168 E. 88th St.;160 E. 88th St."""
# --- Group B: DOH 07-10, remediation expected by 07-11 (12) ---
B = """1875 Second Ave.;1110 Fifth Ave.;153 E. 78th St.;135 E. 79th St.;300 E. 79th St.;
238 E. 81st St.;160 E. 84th St.;114 E. 85th St.;401 E. 88th St.;333 E. 91st St.;354 E. 91st St.;312 E. 95th St."""
# --- Group C: additional, completed remediation (24) ---
C = """1130 Fifth Avenue;1150 Madison Avenue;1239 Madison Avenue;1275 Madison Avenue;1020 Park Avenue;
1157 Lexington Avenue;1755 York Avenue;60 East End Avenue;188 East 78th Street;200 East 78th Street;
124 East 79th Street;201 East 79th Street;211 East 79th Street;511 East 80th Street;444 East 82nd Street;
500 East 83rd Street;7 East 86th Street;401 East 86th Street;444 East 86th Street;445 East 86th Street;
51 East 87th Street;9 East 90th Street;410 East 92nd Street;40 East 94th Street"""
# --- Group D: additional, ordered to complete by 07-16 (20) ---
D = """980 Fifth Avenue;1000 Fifth Avenue;920 Park Avenue;1249 Park Avenue;1025 Madison Avenue;
1381 Lexington Avenue;1513 First Avenue;1520 York Avenue;80 East End Avenue;90 East End Avenue;
100 East End Avenue;155 East 79th Street;40 East 80th Street;25 East 83rd Street;13 East 84th Street;
40 East 84th Street;108 East 89th Street;22 East 91st Street;200 East 95th Street;235 East 95th Street"""
# --- Group E: unregistered tower sampled, completed (1) ---
E = """300 East 83rd Street"""

GROUPS = [("A_doh0710_complete", A, True), ("B_doh0710_expected", B, True),
          ("C_added_complete", C, True), ("D_added_by0716", D, True),
          ("E_unregistered_complete", E, False)]

def clean(s):
    return re.sub(r"\s+", " ", s.strip())

rows = []
for grp, blob, registered_expected in GROUPS:
    for a in blob.replace("\n", "").split(";"):
        a = clean(a)
        if not a:
            continue
        rows.append({"address_raw": a, "status_group": grp,
                     "registered_expected": registered_expected})

# dedupe check on a loose key (digits + collapsed alpha)
def key(a):
    return re.sub(r"[^a-z0-9]", "", a.lower()
                  .replace("street","st").replace("avenue","ave")
                  .replace("east","e").replace("west","w")
                  .replace("nd","").replace("rd","").replace("th","").replace("st ","")).strip()

seen = {}
for r in rows:
    k = key(r["address_raw"])
    seen.setdefault(k, []).append(r["address_raw"])
dups = {k: v for k, v in seen.items() if len(v) > 1}

RAW.mkdir(parents=True, exist_ok=True)
with open(RAW / "affected_buildings.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["address_raw", "status_group", "registered_expected"])
    w.writeheader(); w.writerows(rows)

print(f"total case buildings: {len(rows)}")
from collections import Counter
for g, c in Counter(r["status_group"] for r in rows).items():
    print(f"  {g}: {c}")
print(f"duplicate loose-keys: {len(dups)}")
for k, v in dups.items():
    print("   DUP:", v)
