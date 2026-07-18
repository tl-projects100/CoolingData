"""Assemble a static site under docs/ for GitHub Pages: a landing hub linking to
the interactive map, both reports, the PDFs, the data, and the GitHub repo."""
import pathlib, shutil, re, markdown
ROOT = pathlib.Path(__file__).resolve().parent.parent
REPORTS, PROC, RAW = ROOT/"reports", ROOT/"data"/"processed", ROOT/"data"/"raw"
DOCS = ROOT/"docs"; (DOCS/"data").mkdir(parents=True, exist_ok=True)
GH = "https://github.com/tl-projects100/coolingdata"

def full_doc(title, body):
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>{title}</title>\n</head>\n<body>\n{body}\n</body>\n</html>\n')

# --- wrap artifact-body pages into full standalone documents ---
for src, dst in [("map.html", "map.html"), ("public_report.html", "report.html")]:
    body = (REPORTS/src).read_text()
    m = re.search(r"<title>(.*?)</title>", body)
    (DOCS/dst).write_text(full_doc(m.group(1) if m else "Report", body))

# --- render technical findings markdown -> styled full page ---
FCSS = """
:root{--bg:#f4f5f3;--surface:#fff;--ink:#17181a;--ink2:#4a4f55;--line:#e3e5e4;--accent:#b4531f;--code:#f1f0ec}
@media(prefers-color-scheme:dark){:root{--bg:#101214;--surface:#181b1e;--ink:#f0f2f3;--ink2:#bfc5cb;--line:#2b3034;--accent:#f0793f;--code:#202427}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
 font-family:-apple-system,system-ui,"Segoe UI",Roboto,sans-serif;line-height:1.6}
.wrap{max-width:820px;margin:0 auto;padding:32px 20px 80px}
h1{font-family:Georgia,serif;font-size:2rem;line-height:1.1;margin:.2em 0}
h2{font-family:Georgia,serif;font-size:1.4rem;margin:1.6em 0 .4em;padding-top:.5em;border-top:2px solid var(--line)}
h3{font-size:1.05rem;color:var(--accent);margin:1.2em 0 .3em}
p,li{font-size:.98rem}a{color:var(--accent)}
code{font-family:ui-monospace,Menlo,monospace;font-size:.85em;background:var(--code);padding:1px 5px;border-radius:4px}
pre{background:var(--code);padding:12px 14px;border-radius:8px;overflow-x:auto;font-size:.8rem}
table{border-collapse:collapse;width:100%;margin:14px 0;font-size:.85rem;display:block;overflow-x:auto}
th,td{border:1px solid var(--line);padding:6px 10px;text-align:left}th{background:var(--code)}
blockquote{margin:14px 0;padding:10px 16px;background:var(--code);border-left:3px solid var(--accent);border-radius:0 8px 8px 0}
.back{display:inline-block;margin-bottom:18px;font-size:.85rem}
"""
md = (REPORTS/"findings.md").read_text()
html = markdown.markdown(md, extensions=["tables","fenced_code","sane_lists"])
(DOCS/"findings.html").write_text(full_doc(
    "Technical Findings — UES Legionnaires × Cooling Towers",
    f'<style>{FCSS}</style><div class="wrap"><a class="back" href="./">← back to overview</a>{html}</div>'))

# --- copy PDFs + data ---
shutil.copy(REPORTS/"UES_Legionnaires_explainer.pdf", DOCS/"explainer.pdf")
shutil.copy(REPORTS/"UES_Legionnaires_technical_findings.pdf", DOCS/"technical-findings.pdf")
DATA = [(RAW/"affected_buildings.csv","affected_buildings.csv"),
        (PROC/"analysis_table.csv","analysis_table.csv"),
        (PROC/"analysis_table_pluto.csv","analysis_table_pluto.csv"),
        (REPORTS/"odds_ratios.csv","odds_ratios_primary.csv"),
        (REPORTS/"odds_ratios_pluto.csv","odds_ratios_pluto.csv"),
        (REPORTS/"map_data.json","map_points.json")]
for src, dst in DATA:
    if src.exists(): shutil.copy(src, DOCS/"data"/dst)
(DOCS/".nojekyll").write_text("")   # serve files as-is

# --- landing hub ---
INDEX = f"""<style>
:root{{--bg:#eceae4;--surface:#faf9f6;--surface2:#efeee9;--ink:#16181b;--ink2:#4a4f55;--ink3:#7c828a;
 --line:#e3e5e4;--case:#c9531f;--control:#2565c4;--shadow:0 1px 2px rgba(0,0,0,.05),0 10px 30px rgba(0,0,0,.07);
 --serif:ui-serif,Georgia,serif;--sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
 --mono:ui-monospace,"SF Mono",Menlo,monospace}}
@media(prefers-color-scheme:dark){{:root{{--bg:#101214;--surface:#181b1e;--surface2:#202427;--ink:#f0f2f3;
 --ink2:#bfc5cb;--ink3:#868d95;--line:#2b3034;--case:#f0793f;--control:#5896ec}}}}
*{{box-sizing:border-box}}body{{margin:0}}
.pg{{font-family:var(--sans);background:var(--bg);color:var(--ink);min-height:100vh;
 padding:clamp(24px,5vw,64px) 20px 80px;line-height:1.6}}
.col{{max-width:760px;margin:0 auto}}
.eyebrow{{font-family:var(--mono);font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--case);margin:0 0 12px}}
h1{{font-family:var(--serif);font-weight:600;font-size:clamp(1.9rem,5vw,2.9rem);line-height:1.05;margin:0 0 14px;letter-spacing:-.02em}}
.dek{{font-size:1.12rem;color:var(--ink2);margin:0 0 10px;max-width:60ch}}
.note{{font-size:.85rem;color:var(--ink3);margin:0 0 28px}}
.grid{{display:grid;gap:14px;margin:26px 0}}
@media(min-width:640px){{.grid{{grid-template-columns:1fr 1fr}}}}
.card{{display:block;text-decoration:none;color:inherit;background:var(--surface);border:1px solid var(--line);
 border-radius:16px;padding:22px 24px;box-shadow:var(--shadow);transition:transform .12s,border-color .12s}}
.card:hover{{transform:translateY(-2px);border-color:var(--ink3)}}
.card .ic{{font-size:1.6rem}}
.card h2{{font-family:var(--serif);font-size:1.3rem;margin:10px 0 6px}}
.card p{{font-size:.92rem;color:var(--ink2);margin:0}}
.card.wide{{grid-column:1/-1}}
.sub{{font-family:var(--mono);font-size:.72rem;color:var(--ink3);margin-top:10px;letter-spacing:.03em}}
.row{{display:flex;flex-wrap:wrap;gap:10px;margin:8px 0 30px}}
.btn{{font:inherit;font-size:.9rem;text-decoration:none;color:var(--ink);background:var(--surface2);
 border:1px solid var(--line);border-radius:999px;padding:8px 16px;display:inline-flex;gap:7px;align-items:center}}
.btn:hover{{border-color:var(--ink3)}}
h3.sec{{font-family:var(--serif);font-size:1.15rem;margin:30px 0 6px}}
.foot{{border-top:1px solid var(--line);margin-top:40px;padding-top:20px;font-size:.82rem;color:var(--ink3);max-width:70ch}}
.foot code{{font-family:var(--mono);font-size:.9em}}
.disc{{background:var(--surface2);border-radius:12px;padding:14px 16px;margin-top:16px;font-size:.8rem;color:var(--ink3)}}
a{{color:var(--case)}}
</style>
<div class="pg"><div class="col">
  <p class="eyebrow">Independent analysis · NYC Open Data</p>
  <h1>Upper East Side Legionnaires' &times; cooling-tower data</h1>
  <p class="dek">Do the 76 UES buildings ordered to clean their cooling towers in the 2026
  Legionnaires' cluster differ from their neighbors in the public record? A reproducible
  analysis of NYC Open Data — with an interactive map, a plain-language explainer, and the
  full technical write-up.</p>
  <p class="note">Not affiliated with or endorsed by the NYC Health Department. For official
  guidance, see <a href="https://www.nyc.gov/site/doh/health/health-topics/legionnaires-disease.page">nyc.gov/health</a> or call 311.</p>

  <div class="grid">
    <a class="card" href="report.html"><div class="ic">💧</div>
      <h2>Read the explainer</h2><p>Plain-language walkthrough: what the data shows,
      why the "40%" is a testing artifact, and the factors we couldn't measure.</p>
      <div class="sub">HTML · plain language</div></a>
    <a class="card" href="map.html"><div class="ic">🗺️</div>
      <h2>Explore the map</h2><p>Every registered cooling tower in the outbreak ZIPs over the
      NYC street grid. Tap a building for its history.</p>
      <div class="sub">HTML · interactive</div></a>
    <a class="card wide" href="findings.html"><div class="ic">📊</div>
      <h2>Technical findings</h2><p>Full methodology and results: matching, ~40 predictors
      across six datasets, logistic regression, spatial tests, and honest limitations.</p>
      <div class="sub">HTML · detailed</div></a>
  </div>

  <h3 class="sec">Download</h3>
  <div class="row">
    <a class="btn" href="explainer.pdf">⬇︎ Explainer (PDF)</a>
    <a class="btn" href="technical-findings.pdf">⬇︎ Technical findings (PDF)</a>
  </div>

  <h3 class="sec">Data &amp; code</h3>
  <div class="row">
    <a class="btn" href="{GH}">⌥ GitHub repository</a>
    <a class="btn" href="data/affected_buildings.csv">76 affected buildings (CSV)</a>
    <a class="btn" href="data/analysis_table.csv">Analysis table (CSV)</a>
    <a class="btn" href="data/odds_ratios_primary.csv">Odds ratios (CSV)</a>
    <a class="btn" href="data/map_points.json">Map points (JSON)</a>
  </div>

  <div class="foot">
    <p><b>Sources.</b> NYC Cooling Tower Registrations (<code>y4fw-iqfr</code>), Cooling Tower
    Inspections (<code>f9wb-g8mb</code>), PLUTO (<code>64uk-42ks</code>), DOB/HPD violations,
    LL84 benchmarking, Street Centerline (<code>inkn-q76z</code>) — all via
    <a href="https://opendata.cityofnewyork.us">NYC Open Data</a> — plus the NYC DOH
    clean-and-disinfect list. Reproduce with the scripts in the repo (<code>src/</code>).</p>
    <div class="disc"><b>Independent analysis — not an official record.</b> Outcome is cooling-tower
    positivity, not human illness; patient locations are private. Findings are exploratory and
    limited by public data. Nothing here is medical advice.</div>
  </div>
</div></div>"""
(DOCS/"index.html").write_text(full_doc("UES Legionnaires' × Cooling Towers — Overview", INDEX))
print("built docs/:", sorted(p.name for p in DOCS.iterdir()))
print("docs/data/:", sorted(p.name for p in (DOCS/'data').iterdir()))
