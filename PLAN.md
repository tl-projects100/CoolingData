# Legionnaires' × Cooling-Tower History — Plan of Attack

**Question:** Is there a relationship between the NYC buildings implicated in the
2026 Upper East Side Legionnaires' cluster and those buildings' cooling-tower
registration / inspection / testing history?

**Date:** 2026-07-17 · Branch: `claude/legionnaires-cooling-data-nyc-i0bbed`

---

## 0. What we're actually modeling (read this first)

The press-release list is **buildings ordered to clean & disinfect because their
cooling tower PCR-tested positive for *Legionella*** during the outbreak
investigation — it is *not* a list of where sick people live (patient addresses
are never published, for privacy). So the honest outcome variable is:

> **Did this building's cooling tower test positive for *Legionella* during the
> 2026 UES investigation? (yes/no)**

The analysis is therefore a **case–control study of cooling towers**: compare the
compliance/testing history of positive ("case") towers against negative
("control") towers, and ask which historical factors are associated with
testing positive. This is the defensible framing for a "multi-factorial
regression." We will state this scoping explicitly in the writeup so we don't
overclaim a link to human illness.

## 1. Outbreak context (from news + DOH, July 2026)

- Cluster in Carnegie Hill / Yorkville (UES), ZIPs **10028, 10128, 10075**.
- ~63 confirmed human cases as of 2026-07-14; dozens hospitalized.
- Reports cite ~31 buildings (initial PCR screen) growing to ~76 tower-positive
  buildings — the press-release "preliminary list" is our case set.

## 2. Data sources (NYC Open Data / Socrata)

| Role | Dataset | ID | Notes |
|---|---|---|---|
| Registrations + Legionella sample dates | NYC Cooling Tower Registrations | `y4fw-iqfr` | current commissioned towers; `Sample_Dates`, geocodes, BIN/BBL |
| Regulatory inspections + violations | NYC Cooling Tower System Inspection Results | `f9wb-g8mb` | 2017→, cycle/non-cycle, violation/citation; ~6-mo posting lag |
| Case set | DOH preliminary clean/disinfect list | press release (HTML) | scrape → addresses; geocode/match to BIN |
| (Optional) statewide registry | NYS Cooling Tower Registry | `gd58-9fej` | cross-check / extra attributes |
| (Optional) building attributes | PLUTO | `64uk-42ks` | year built, floors, use, assessed value by BBL |

Socrata access pattern (with an app token to avoid throttling):
`https://data.cityofnewyork.us/resource/y4fw-iqfr.json?$where=...&$limit=50000`

## 3. Feature engineering (per building/tower, all as-of just before the outbreak)

From registrations (`y4fw-iqfr`):
- days since **last** Legionella sample; count of samples in trailing 12/24 mo;
  max gap between samples; whether sampling cadence met the 90-day / new monthly rule.
- tower count at the building; active vs inactive equipment; registration age.

From inspections (`f9wb-g8mb`):
- # inspections (2017→); # with violations; # citations; days since last
  inspection; ever-cited flag; violation rate.

Geospatial / building:
- ZIP, community board, census tract, NTA; lat/long.
- distance to nearest other positive tower; local density of towers.
- (PLUTO) year built, #floors, building area, land use.

## 4. Analysis design

**A. Join & QA.** Match case addresses → registrations by BIN/BBL, with
address-normalization + geocode fallback (fuzzy match, manual audit of misses).
Label each registered tower case=1 / control=0.

**B. Control-group definition (decide up front — biases the whole result):**
- *Primary:* all registered towers in the three outbreak ZIPs (tight geographic
  control — reduces confounding by neighborhood).
- *Sensitivity:* all Manhattan towers, with borough/ZIP adjustment.

**C. EDA / descriptive.**
- positivity rate by ZIP / community board / NTA; maps (folium/kepler).
- distributions of each feature, case vs control; missingness report.
- correlation heatmap; check multicollinearity (VIF).

**D. Univariate association.** Per feature: chi-square / Fisher (categorical),
t-test or Mann-Whitney (continuous); report effect sizes, not just p-values.

**E. Multi-factorial (multivariable) regression — the core deliverable.**
- **Logistic regression**: `positive ~ days_since_last_sample + n_violations +
  days_since_last_inspection + tower_count + year_built + zip + ...`
- Report **odds ratios + 95% CIs**; check calibration & AUC.
- **Guard against overfitting** (only ~31–76 cases): keep predictors few
  (rule of thumb ≥10 events per predictor), and run **penalized logistic
  (L1/LASSO)** or **Firth** as the robust companion model.
- Multiple-testing note; pre-register the primary model to avoid p-hacking.

**F. Spatial checks.** Moran's I on residuals (spatial autocorrelation);
if present, add spatial term / cluster-robust SEs — cases are geographically
clustered *by construction*, so this matters.

**G. Recommended extras.**
- Time-to-event view: survival on "time since last valid sample."
- Simple tree / gradient-boost for nonlinear feature importance (as a
  cross-check on the logistic model, not the headline).
- Negative-control period / placebo test where feasible.

## 5. Honest limitations (put in the report)

Outcome = tower positivity, not human infection · tiny case count → wide CIs ·
selection & surveillance bias (positive towers were *sought* in these ZIPs) ·
ecological fallacy · ~6-month inspection-data lag may miss recent history ·
address→BIN match error · association ≠ causation.

## 6. Deliverables & repo layout

```
data/raw/            # pulled Socrata JSON/CSV + scraped case list (git-ignored if large)
data/processed/      # joined, labeled analysis table
notebooks/           # 01_eda, 02_features, 03_regression, 04_spatial
src/                 # fetch_socrata.py, scrape_pressrelease.py, features.py, models.py
reports/             # findings.md + figures + an HTML/interactive map
requirements.txt
PLAN.md
```
Stack: Python — `pandas`, `requests`/`sodapy`, `statsmodels`, `scikit-learn`,
`geopandas`, `folium`, `matplotlib`. Reproducible: one `make data` / `make analysis`.

## 7. Phases

1. **Ingest** — pull the 3 sources (registrations, inspections, DOH list).
2. **Match & label** — build the case/control analysis table + QA report.
3. **EDA** — descriptives, maps, association tests.
4. **Regression** — logistic + penalized, ORs, diagnostics.
5. **Spatial + extras** — autocorrelation, robustness.
6. **Report** — findings.md + figures + interactive map; commit & push.
