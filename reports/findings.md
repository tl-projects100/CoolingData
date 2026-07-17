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
