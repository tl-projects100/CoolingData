# Legionnaires' × Cooling-Tower History — Findings

**2026 Upper East Side (UES) Legionnaires' disease community cluster**
Analysis date: 2026-07-17 · Data: NYC Open Data (Socrata) + DOH press-release list

---

## 1. Question and framing

Is there a relationship between the NYC buildings implicated in the 2026 UES
Legionnaires' cluster and those buildings' cooling-tower **registration,
Legionella-sampling, and inspection history**?

The DOH "clean & disinfect" list is a roster of **buildings whose cooling
tower(s) tested PCR-positive for *Legionella*** during the July 2026
investigation — not patient addresses (those are never published). So this is a
**case–control study of cooling towers**:

> **Outcome:** building's tower(s) PCR-positive & ordered to remediate (case=1) vs not (control=0)
> **Exposures:** historical compliance / maintenance features engineered from the two open datasets.

## 2. Data

| Dataset | Socrata ID | Rows pulled |
|---|---|---|
| NYC Cooling Tower Registrations (+ Legionella sample dates) | `y4fw-iqfr` | 5,949 |
| NYC Cooling Tower System Inspection Results | `f9wb-g8mb` | 122,846 |
| DOH affected-building list (31 on 07-10 + 45 update) | press release | **76 buildings** |

All 76 case addresses matched to a registered building (BIN) after address
normalization — **0 unmatched**. (Sanity checks: 1000 Fifth Ave = 21 towers = the
Met; "300 E 83rd", flagged "unregistered" by DOH, does appear in registrations.)

**Leakage control:** every history feature is capped at **2026-07-01** — the
July-2026 investigation samples *are* the outcome, so including them would leak it.

## 3. Design & sample

Positivity is overwhelmingly a function of **being in the sampled area**:

| Area | Buildings | Positivity |
|---|---|---|
| Outbreak ZIPs (10028 / 10075 / 10128) | 183 | **40.4%** |
| Rest of Manhattan | 2,699 | 0.07% |

Buildings outside the zone were never sampled, so counting them as "controls"
would be surveillance bias. **Primary analysis is therefore restricted to the
183 registered buildings in the outbreak ZIPs (74 cases, 109 controls).**

## 4. Results

### 4a. Univariate (case vs control, in zone)
Significant / notable (Mann-Whitney or Fisher):

| Feature | Case (median) | Control (median) | p |
|---|---|---|---|
| Registration age (yrs) | 10.8 | 10.8 | **0.003** |
| # Legionella samples (24 mo) | 4 | 3 | **0.010** |
| Median gap between samples (days) | 41.5 | 54.5 | **0.025** |
| Days since last sample | 16 | 20 | 0.27 |
| # Violations (all-time) | 17 | 16 | 0.37 |
| Ever cited for a violation | 93% | 94% | 1.00 |
| Overdue >90d on sampling | 9% | 18% | 0.14 |

Direction is the opposite of a naïve "negligence" hypothesis: case towers were
sampled **more** often and had **shorter** gaps, not fewer. Violation/citation
history did **not** differ.

### 4b. Multivariable logistic regression (primary model)
183 buildings, 74 cases, 6 predictors, all VIF < 2.2. ORs are per **1 SD**
(continuous). Figure: `reports/figures/odds_ratios.png`.

| Predictor | OR | 95% CI | p |
|---|---|---|---|
| Registration age | **1.57** | 0.99–2.49 | 0.053 |
| # samples (24 mo) | **1.49** | 0.94–2.35 | 0.089 |
| # violations | 1.13 | 0.78–1.63 | 0.51 |
| Days since last inspection | 0.81 | 0.58–1.12 | 0.20 |
| # towers | 1.00 | 0.65–1.54 | 0.99 |
| Days since last sample | 0.96 | 0.63–1.46 | 0.86 |

Model: McFadden R² = 0.065, in-sample AUC = 0.70, joint LLR p = 0.013.

**L1/LASSO companion** (guards against overfitting): keeps the same two leading
signals — registration age (OR ≈ 1.53) and sampling frequency (OR ≈ 1.46) —
shrinks # towers to zero. Cross-validated AUC ≈ 0.60 (weak).

### 4c. Spatial autocorrelation
Moran's I (binary weights, 400 m): case indicator **I = 0.0004, p = 0.15**;
model residuals **I ≈ 0, p = 0.38**. **No fine-scale spatial clustering** of
positive towers within the zone — positives and negatives are intermixed
(`reports/figures/map_towers.png`).

### 4d. PLUTO sensitivity (building attributes)
Joining PLUTO by BBL (173/183 zone buildings matched), **case buildings are
physically bigger and higher-valued**, not older:

| Attribute | Case (median) | Control (median) | p |
|---|---|---|---|
| Assessed total value | \$21.2M | \$14.7M | **0.004** |
| Building floor area | 144,280 | 106,034 | **0.025** |
| # Floors | 18 | 16 | **0.046** |
| Building age (yrs) | 62 | 63 | 0.48 |

Re-running the logistic model with PLUTO covariates added
(`reports/odds_ratios_pluto.csv`): the **registration-age signal attenuates to
null** (OR 1.20, p=0.38) — it was partly a proxy for building size/value — while
**sampling frequency stays significant** (OR 1.52, p=0.023) and assessed value
trends positive (OR 1.49, p=0.091). Model AUC 0.71, R² 0.072. So the most robust
correlate of positivity is *how much a tower is sampled*, plausibly detection
intensity, with building size/value as a secondary axis.

### 4e. Tier-1 additional predictors
Nine further hypotheses were tested (`src/tier1.py`,
`reports/odds_ratios_tier1.csv`): severity-split violations (PHH / Critical),
Legionella / water-quality–specific violations, follow-up ("non-cycle")
inspections, local cooling-tower density within 200 m, sampling-cadence
regularity, and ever-inactive status.

| New predictor | Case vs control | p |
|---|---|---|
| Ever had a **follow-up ("non-cycle") inspection** | 35% vs 20% | **0.027** |
| # non-cycle inspections | higher in cases | **0.015** |
| Water-quality / Legionella violations (focused model) | OR 1.68 / SD | 0.106 |
| Local tower density (200 m) | 10 vs 10 | 0.60 (null) |
| PHH / Critical violation counts | — | 0.59 / 0.24 (null) |
| Sampling-cadence irregularity (gap CV) | 0.82 vs 0.68 | 0.15 (null) |
| Ever-inactive tower | 4% vs 6% | 0.74 (null) |

The one nominal signal is **follow-up inspections** — complaint- or
problem-triggered visits, i.e. buildings previously flagged. In the focused
6-predictor model (n=183) **sampling frequency remains the most robust
correlate** (OR 1.58, p=0.017); water-quality violations trend positive but are
not significant; AUC 0.66.

> **Multiple-comparison caveat:** ~9 features were tested, so ~0.5 false
> positives are expected at α=0.05. The non-cycle signal (p≈0.02) does **not**
> survive a Bonferroni correction (~0.006) and should be read as a lead to
> investigate, not a finding. Tower density being null is itself informative:
> positive towers are **not** concentrated where towers are densest.

### 4f. Tier-2 additional data (LL84 energy/water · DOB · HPD)
Pulled three more open datasets and joined by BBL to the zone (`src/tier2.py`):
LL84 benchmarking (`5zyy-y8am`; energy/water use as a cooling-load proxy), DOB
violations (`3h2n-5cm9`), and HPD housing violations (`wvxf-dwi5`).

| New predictor | Case vs control (median) | p |
|---|---|---|
| **# DOB violations (all-time)** | 53 vs 35 | **0.0004** |
| Site energy-use intensity (EUI) | 82.5 vs 72.6 | 0.094 |
| Water use (kgal) — *tower makeup-water proxy* | 4,670 vs 4,214 | 0.33 (null) |
| Water-use intensity (kgal/ft²) | — | 0.85 (null) |
| Energy Star score | 44 vs 40 | 0.62 (null) |
| # HPD violations / Class C (hazardous) | 3 vs 3 / 0 vs 0 | 0.68 / 0.41 (null) |

**DOB violations are the strongest raw signal in the whole study — and a textbook
confounder.** They vanish once building size is controlled:

| Model | DOB odds ratio / SD | p |
|---|---|---|
| DOB alone | 1.60 (1.06–2.43) | 0.026 |
| DOB + assessed value + # towers | 1.22 (0.74–2.01) | 0.43 |
| + building age | 1.18 (0.78–1.79) | 0.44 |

Bigger, older buildings simply accumulate more DOB violations — so the "positive
buildings have more violations" pattern is a **size artifact, not negligence**,
the same confound seen throughout (§4d). Notably, the **cooling-load proxies
themselves — water use and energy intensity — did not hold up** (water null;
EUI attenuates after adjustment), so heavier air-conditioning use is not a clear
driver either. The focused Tier-2 model reaches AUC 0.75 but on a reduced sample
(n=103, LL84 coverage), and the durable signals are still detection-related
(sampling frequency; recency of inspection).

### 4g. Tier-3: construction proximity (null)
Current DOB NOW permits (`rbx6-tga4`, `src/tier3_construction.py`) in the UES
bounding box: **45,020 permits**. The neighborhood is so densely permitted that
every building sits a median **~740 permits within 150 m**. Distance to nearest
construction (p=0.57) and permit density within 150 m (p=0.28) were both null —
in a saturated area, construction proximity can't discriminate cases from controls.

### 4h. Full predictor inventory (~40 variables tested)

| Domain | Variables tested | Verdict |
|---|---|---|
| **Tower testing history** | # samples (12/24 mo), days since last sample, sampling gaps + irregularity, overdue-90d, never-sampled | null — except **sampling *frequency*** (↑ in cases, detection signal) |
| **Tower inspections** | # inspections, days since last, cycle vs **non-cycle**, ever-inactive | null — except **follow-up (non-cycle)** inspections (weak, not MC-robust) |
| **Tower violations** | total, ever-cited, # types, **Critical**, **PHH**, **Legionella/water-quality** | **all null** |
| **Building physical** (PLUTO) | year built/age, # floors, res/total units, **floor area**, **assessed value** | size/value ↑ in cases → **confounder**, not negligence |
| **Energy / water** (LL84) | site & source EUI, **water use**, water intensity, Energy Star | null / weak (cooling-load proxy did **not** hold) |
| **Management quality** | **DOB violations**, HPD violations, HPD Class-C | DOB significant alone but **erased by size adjustment**; HPD null |
| **Spatial / context** | outbreak-ZIP, **tower density (200 m)**, Moran's I, **construction proximity** | ZIP dominates; within-zone density & clustering **null** |

**Two things survive everything:** *location* (being in the sampled zone) and
*detection intensity* (how often a tower is looked at). Every negligence-flavored
variable is null or dissolves under size adjustment.

### 4i. Tier-4 advanced designs & angles

Beyond more predictors, we ran different *questions and study designs*
(`src/tier4_*.py`):

| Angle | Method | Result |
|---|---|---|
| **#7 Matched case-control** | 63 case↔control pairs matched on size/value/age; paired tests on compliance | **Confirms negligence-null**: violations still null (p=0.85); only **more sampling** (p=0.026) and **more recent inspection** (p=0.009) survive — detection signals, not maintenance |
| **#3 Directional gradient** | trend-surface logistic on projected coords | **New (weak) signal**: positivity rises to the **north** (N–S OR 2.0/km, p=0.043; bearing ~336°; joint p=0.068) — a gradient Moran's I is blind to |
| **#8 "Lottery" model** | binomial P(pos)=1−(1−p)^towers vs constant | Lottery **rejected** (LR p=0.44); tower *count* doesn't drive positivity → per-tower conditions do |
| **#1/#2 Owner/contractor network** | shared PLUTO owner + DOB permit contractor across the 76 | **Null** — buildings are single-asset LLCs; shared contractors (scaffolding/mechanical) appear equally on controls. *Water-treatment vendor — the relevant one — isn't in open data* |
| **#5 Repeat-offenders / prior clusters** | prior Legionella violations; past NYC cluster geographies | **Null / no overlap** — Legionella-specific violations flat (§4e); prior NYC clusters were in the Bronx/Upper Manhattan (different geography) |
| **#6 Weather trigger** | July-2026 timeline vs conditions | **Consistent** with an environmental bloom — the cluster coincided with a heat wave that officials linked to Legionella growth (qualitative) |
| **#9 Real outcome / tower hardware** | NYS registry `gd58-9fej`; NYC results fields | **Unavailable** — datasets are dates-only (no results); NYS registry is a 74-row upstate sample with no NYC coverage, so manufacturer/model/capacity can't be joined |
| **#4 Aerosol plume model** | Gaussian plume vs case locations | **Not feasible** on open data — requires patient coordinates (private); the #3 gradient is the available substitute |

**Takeaways:** (1) the negligence-null now survives a *matched* design — the
cleanest test — so it is not a size artifact; (2) the only genuinely new positive
result is a **weak northward gradient** in positivity, worth noting but borderline
and unadjusted for multiple looks; (3) every mechanistic link we *could* build
from open data (ownership, contractors, tower hardware, prior history) is null or
unavailable, reinforcing that the deciding variables are tower-level and
unpublished (§5b).

## 5. Interpretation

1. **The dominant "predictor" of a positive tower is geography, not maintenance
   history** — 40% positivity in-zone vs ~0% elsewhere. This is consistent with a
   diffuse neighborhood aerosol exposure, reinforced by the flat Moran's I (no
   single point-source hotspot within the zone).
2. **Within the outbreak zone, compliance history explains little** (AUC 0.70,
   R² 0.07). Crucially, the metrics a regulator would flag — violations,
   citations, overdue sampling, sparse inspections — were **not** associated with
   testing positive. This argues the cluster is **not** simply a "negligent
   operators" story.
3. The two weak positive associations both plausibly reflect **detection/confounding,
   not causation**: towers sampled more frequently are more likely to *catch* a
   positive (surveillance intensity), and older registrations proxy for older/larger
   building systems. Neither is evidence that more testing *causes* Legionella.

**Bottom line:** there is a modest, statistically borderline relationship between
a building's cooling-tower history and outbreak positivity, but it is weak, points
opposite to a negligence hypothesis, and is dwarfed by location. The data do not
support singling out poorly-maintained towers as the driver of this cluster.

### 5b. Why positivity isn't "random" — the variables open data can't see

"Not explained by our variables" is **not** the same as "random." Three real,
non-random drivers *are* in the data: **location**, **building scale**, and
**detection intensity**. What's genuinely flat is the *negligence/compliance* axis.

The reason the within-zone pattern still looks like scatter is that **whether a
given tower blooms is decided by tower-level operational conditions that no public
dataset records.** The registration data lists the *dates* a tower was sampled —
never the *results*. The deciding factors live one layer below open data:

- **Water temperature** in the basin (the dominant growth factor)
- **Biocide/treatment dosing** and any lapse in it
- **Stagnation** — short idle periods, dead legs, a pump cycling off
- **Biofilm / scale**, and **drift-eliminator** condition (how much mist escapes)
- **Nutrient load** and makeup-water quality
- **Exact timing** of the last real cleaning relative to the July heat
- **Tower make / model / design** — some aerosolize far more than others

Two buildings identical on every public field can differ entirely on these — and
*that* is what separates a positive tower from a negative one. Legionella clusters
are characteristically idiosyncratic per-tower plus weather plus chance; this kind
of within-area scatter is exactly what the epidemiology predicts.

**Power:** with 74 cases we can only detect *large* effects; a real OR≈1.3 would
need several hundred cases. "Null" means "no large effect visible in building-level
open data," not "no effect exists." We are also using **building-level administrative
records** to chase a **tower-level microbiological** event — an inherent ceiling.

**What would actually explain which towers bloomed** (and what DOH uses internally,
unpublished): per-tower *Legionella* culture counts over time; water-treatment and
maintenance logs; tower make/model/age; and — the gold standard — **genomic matching**
of each tower's isolate to patient isolates. A regression on open data structurally
cannot name the source; it can only rule hypotheses in or out, which is what we did.

## 6. Limitations

- Outcome = **tower positivity**, not human infection (patient addresses private).
- Small case count (74 in-zone) → wide CIs; borderline p-values are fragile.
- **Surveillance/detection bias:** positives were actively *sought* in these ZIPs.
- ~6-month posting lag on inspections; owner-reported sample dates may be imperfect.
- Registration age is a proxy (date first registered ≈ 2015 floor), not true tower age.
- Association ≠ causation; ecological/aggregation caveats apply.

## 7. Reproducibility

```
python3 src/fetch_data.py        # pull Socrata datasets -> data/raw/
python3 src/build_case_list.py   # 76-building case roster -> data/raw/
python3 src/match_and_label.py   # address match/audit -> data/processed/
python3 src/build_features.py    # labeled feature table -> data/processed/
python3 src/analyze.py           # EDA + regression + spatial -> reports/
python3 src/enrich_pluto.py      # PLUTO join + sensitivity model -> reports/
python3 reports/build_map.py     # self-contained artifact map (NYC grid basemap)
python3 reports/build_leaflet.py # standalone map w/ OpenStreetMap tiles (open locally)
```
Console logs: `reports/stats.txt`, `reports/stats_pluto.txt`. Odds ratios:
`reports/odds_ratios.csv`, `reports/odds_ratios_pluto.csv`.

## 8. Interactive maps

- **`reports/map.html`** — self-contained interactive dot-map over the authentic NYC
  street grid (basemap from NYC Open Data `inkn-q76z`); hover history, filters, table
  view; works inside a sandboxed artifact (no external requests).
- **`reports/map_leaflet.html`** — standalone map on a live OpenStreetMap tile
  basemap; open in a browser locally (loads external tiles, so not for the sandbox).

*When the DOH list grows further, drop the new addresses into
`src/build_case_list.py` and re-run — the pipeline is a drop-in re-run.*
