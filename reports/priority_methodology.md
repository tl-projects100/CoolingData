# Testing-Priority Score — Methodology

*A transparent heuristic for prioritizing **which registered cooling towers to
test or inspect next**. It is **not** a prediction that any building has
*Legionella*.*

---

## What this is — and what it is not

**Is:** a way to rank registered cooling-tower buildings by public *compliance and
monitoring* signals, so limited inspection/testing effort can focus on the biggest
**blind spots** first.

**Is not:** a risk model for *Legionella* presence. The factors that actually drive
growth in a cooling tower — water temperature, biocide dosing and lapses,
stagnation, biofilm, tower make/model — are **not in any public dataset**, and the
building-level model these signals come from is weak (area-under-curve ≈ 0.70). A
high score means "under-monitored, with a history worth a look," not "dangerous."

## Inputs (all public — NYC Open Data)

- **Cooling Tower Registrations** (`y4fw-iqfr`) — tower counts and Legionella
  water-sample dates.
- **Cooling Tower Inspection Results** (`f9wb-g8mb`) — inspection dates and
  violations, including water-quality / Legionella-specific violations.

All signals are computed **as-of before the investigation window** (capped
2026-07-01) so the outbreak's own sampling can't leak into the score.

## The score

Each building is scored on four factors. Every factor is converted to a **0–1
percentile** within the population being ranked (so the score is relative, not an
absolute risk), then combined as a weighted sum:

| Factor | What it captures | Weight |
|---|---|---|
| **Overdue sampling** — days since last Legionella test (never-sampled = worst) | monitoring blind spot | **0.35** |
| **Water-quality / Legionella violations** (all-time count) | documented past water-management problems | **0.30** |
| **Inspection gap** — days since last inspection (never = worst) | oversight blind spot | **0.20** |
| **Tower count** | consequence/exposure if it *did* bloom (bigger plume) | **0.15** |

`priority = 0.35·overdue + 0.30·violations + 0.20·inspection_gap + 0.15·towers`

Buildings are ranked high→low. Missing "days since" values (a building never
sampled or never inspected) are treated as the worst case — those are exactly the
blind spots the score is meant to surface. Weights are a deliberate, editable
choice, not a fitted result; anyone can re-weight to match their priorities.

## How to read a ranking

- A top rank usually means **overdue or never-tested**, *and* carrying a
  water-quality violation history — a legitimate reason to **look**, not proof of
  anything.
- The order is a **triage aid**, not a danger ranking. Two buildings a few places
  apart are effectively tied given the underlying uncertainty.
- Because the signals are largely *detection/compliance*, the score will tend to
  surface diligent-but-overdue buildings and larger systems — read it as "where
  monitoring has gaps," and pair it with actual testing before drawing conclusions.

## Limitations

- No public dataset contains the variables that determine *Legionella* growth, so
  this cannot be a true risk model.
- The parent case-control model is underpowered (only ~74 outbreak cases) and its
  associations are weak and largely confounded by building size.
- Percentiles are **relative to the group scored** — a "high" score in one ZIP is
  not comparable to another area with different testing norms.
- Association ≠ causation; a score is a prompt to investigate, nothing more.

## Reproducibility

Compute the four factors from the two registration/inspection datasets, percentile-
rank each within your chosen population (a ZIP, a borough, citywide), apply the
weights above, and sort. Any spreadsheet or a few lines of Python reproduce it.

> **Not an official record.** This methodology is an independent analytical aid,
> not affiliated with the NYC Health Department, and produces no determination
> about any specific building. For official information, see nyc.gov/health or call 311.
