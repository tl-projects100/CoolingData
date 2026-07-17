"""EDA + multi-factorial logistic regression + spatial autocorrelation for the
2026 UES Legionnaires' cooling-tower case-control analysis.

Primary sample: registered cooling-tower buildings in the outbreak ZIPs
(10028/10075/10128). Outcome: building's tower(s) tested PCR-positive and were
ordered to clean/disinfect (case=1) vs not (control=0).
"""
import warnings, pathlib, io, sys
import numpy as np, pandas as pd
from scipy import stats
import statsmodels.api as sm
from sklearn.linear_model import LogisticRegressionCV
from sklearn.preprocessing import StandardScaler
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
warnings.filterwarnings("ignore")

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROC, REP = ROOT/"data"/"processed", ROOT/"reports"
FIG = REP/"figures"; FIG.mkdir(parents=True, exist_ok=True)
OUT = io.StringIO()
def log(*a):
    print(*a); print(*a, file=OUT)

df = pd.read_csv(PROC/"analysis_table.csv")
NUM = ["n_towers","n_active_towers","reg_age_days","n_samples","days_since_last_sample",
       "n_samples_12mo","n_samples_24mo","median_gap_days","max_gap_days",
       "n_inspections","n_violations","n_citations","n_violation_types",
       "days_since_last_inspection"]
for c in NUM:
    df[c] = pd.to_numeric(df[c], errors="coerce")
df["reg_age_yrs"] = df["reg_age_days"]/365.25

# ---------- primary sample: outbreak zone ----------
z = df[df["in_outbreak_zip"] == 1].copy()
log("="*70)
log("PRIMARY SAMPLE  = registered cooling-tower buildings in ZIPs 10028/10075/10128")
log(f"  buildings={len(z)}  cases={int(z.case.sum())}  controls={int((z.case==0).sum())}"
    f"  positivity={z.case.mean():.1%}")
log("="*70)

# ---------- missingness ----------
log("\n--- missingness (zone) ---")
for c in NUM:
    m = z[c].isna().mean()
    if m > 0: log(f"  {c}: {m:.1%} missing")

# ---------- univariate association ----------
log("\n--- UNIVARIATE: case vs control (zone) ---")
log(f"{'feature':<26}{'case_med':>10}{'ctrl_med':>10}{'test':>10}{'p':>9}")
uni = []
CONT = ["n_towers","n_active_towers","reg_age_yrs","n_samples","days_since_last_sample",
        "n_samples_24mo","median_gap_days","max_gap_days","n_inspections","n_violations",
        "n_citations","days_since_last_inspection"]
for c in CONT:
    a = z.loc[z.case==1, c].dropna(); b = z.loc[z.case==0, c].dropna()
    if len(a) < 5 or len(b) < 5: continue
    U, p = stats.mannwhitneyu(a, b, alternative="two-sided")
    log(f"{c:<26}{a.median():>10.1f}{b.median():>10.1f}{'MWU':>10}{p:>9.4f}")
    uni.append((c, a.median(), b.median(), p))
BIN = ["never_sampled","overdue_90d","ever_violation"]
for c in BIN:
    ct = pd.crosstab(z[c], z.case)
    if ct.shape == (2,2):
        _, p = stats.fisher_exact(ct.values)
        pr_case = z.loc[z.case==1, c].mean(); pr_ctrl = z.loc[z.case==0, c].mean()
        log(f"{c:<26}{pr_case:>10.2f}{pr_ctrl:>10.2f}{'Fisher':>10}{p:>9.4f}")
        uni.append((c, pr_case, pr_ctrl, p))

# ---------- prep model matrix ----------
z["days_since_last_sample_imp"] = z["days_since_last_sample"].fillna(z["days_since_last_sample"].max())
z["days_since_last_inspection_imp"] = z["days_since_last_inspection"].fillna(z["days_since_last_inspection"].max())
z["ever_inspected"] = (z["n_inspections"] > 0).astype(int)
# NB: overdue_90d is a deterministic function of days_since_last_sample (>90d),
# so the two are collinear -> keep only the continuous recency measure.
PRED = ["n_towers","reg_age_yrs","days_since_last_sample_imp","n_samples_24mo",
        "n_violations","days_since_last_inspection_imp"]
model_df = z.dropna(subset=PRED).copy()
log(f"\n--- multivariable model sample: {len(model_df)} buildings, "
    f"{int(model_df.case.sum())} cases ---")

# --- multicollinearity check (VIF) ---
from statsmodels.stats.outliers_influence import variance_inflation_factor
Xv = sm.add_constant(model_df[PRED].astype(float))
vif = pd.Series([variance_inflation_factor(Xv.values, i) for i in range(Xv.shape[1])],
                index=Xv.columns)
log("\n--- VIF (multicollinearity; >5 = concern) ---")
log(vif.drop("const").round(2).to_string())

# standardize continuous predictors (OR per 1 SD)
CONT_P = ["n_towers","reg_age_yrs","days_since_last_sample_imp","n_samples_24mo",
          "n_violations","days_since_last_inspection_imp"]
sc = StandardScaler()
Xs = model_df[PRED].copy()
Xs[CONT_P] = sc.fit_transform(model_df[CONT_P])
X = sm.add_constant(Xs)
y = model_df["case"].values

# ---------- logistic regression (statsmodels) ----------
log("\n" + "="*70)
log("MULTIVARIABLE LOGISTIC REGRESSION  (standardized: OR per 1 SD; binary: OR)")
log("="*70)
res = sm.Logit(y, X).fit(disp=0)
OR = np.exp(res.params); CI = np.exp(res.conf_int())
tbl = pd.DataFrame({"OR": OR, "CI_low": CI[0], "CI_high": CI[1], "p": res.pvalues})
log(tbl.round(3).to_string())
log(f"\n  pseudo-R2 (McFadden)={res.prsquared:.3f}  n={int(res.nobs)}  "
    f"LLR p={res.llr_pvalue:.2e}")
# AUC (in-sample)
from sklearn.metrics import roc_auc_score
log(f"  in-sample AUC={roc_auc_score(y, res.predict(X)):.3f}")

# ---------- LASSO companion ----------
log("\n--- L1-penalized logistic (LASSO, CV) : robustness / selection ---")
lcv = LogisticRegressionCV(Cs=20, cv=5, penalty="l1", solver="liblinear",
                           scoring="roc_auc", max_iter=5000)
lcv.fit(Xs[PRED], y)
coef = pd.Series(lcv.coef_[0], index=PRED)
log(f"  chosen C={lcv.C_[0]:.4g}   CV-AUC={lcv.scores_[1].mean():.3f}")
log("  nonzero LASSO odds ratios:")
for k, v in coef[coef.abs() > 1e-6].items():
    log(f"    {k:<34} OR={np.exp(v):.3f}")
dropped = list(coef[coef.abs() <= 1e-6].index)
log(f"  shrunk to zero: {dropped if dropped else 'none'}")

# ---------- spatial autocorrelation (Moran's I) ----------
def morans_i(vals, lat, lon, cutoff_m=400.0, nperm=999, seed=1):
    v = np.asarray(vals, float); n = len(v)
    la = np.radians(np.asarray(lat, float)); lo = np.radians(np.asarray(lon, float))
    # equirectangular approx distance in meters
    R = 6371000.0; latm = la.mean()
    x = R*lo*np.cos(latm); ymtr = R*la
    dx = x[:,None]-x[None,:]; dy = ymtr[:,None]-ymtr[None,:]
    D = np.sqrt(dx*dx+dy*dy)
    W = (D>0)&(D<=cutoff_m); W = W.astype(float)  # binary contiguity within cutoff
    rs = W.sum(1); rs[rs==0]=1; Wn = W/rs[:,None]  # row-standardized
    zc = v-v.mean(); denom=(zc*zc).sum()
    def I_(zc): return (n/W.sum())*(zc@(Wn@zc))/denom if W.sum()>0 else np.nan
    I = I_(zc)
    rng=np.random.default_rng(seed); cnt=0
    for _ in range(nperm):
        p=rng.permutation(zc)
        if I_(p) >= I: cnt+=1
    return I, (cnt+1)/(nperm+1), int(W.sum())

log("\n" + "="*70)
log("SPATIAL AUTOCORRELATION  (Moran's I, binary weights, 400 m cutoff)")
log("="*70)
zc = model_df.dropna(subset=["lat","lon"]).copy()
I, p, nlinks = morans_i(zc["case"].values, zc["lat"], zc["lon"])
log(f"  Moran's I (case indicator) = {I:.4f}   perm p = {p:.3f}   links={nlinks}")
# residual autocorrelation (predict on the same standardized design)
Xz = sm.add_constant(pd.DataFrame(sc.transform(zc[CONT_P]), columns=CONT_P, index=zc.index))
resid = zc["case"].values - res.predict(Xz).values
Ir, pr, _ = morans_i(resid, zc["lat"], zc["lon"])
log(f"  Moran's I (model residuals) = {Ir:.4f}   perm p = {pr:.3f}")
log("  (I>0 with small p = spatial clustering; residual clustering = model misses geography)")

# ---------- figures ----------
# 1) map
fig, ax = plt.subplots(figsize=(7,7))
ctrl = zc[zc.case==0]; case = zc[zc.case==1]
ax.scatter(ctrl.lon, ctrl.lat, s=28, c="#5B8DEF", alpha=.7, label="control tower", edgecolor="none")
ax.scatter(case.lon, case.lat, s=48, c="#E4572E", alpha=.85, label="PCR-positive (case)", edgecolor="white", linewidth=.4)
ax.set_title("Registered cooling towers, UES outbreak ZIPs\n(case vs control)")
ax.set_xlabel("longitude"); ax.set_ylabel("latitude"); ax.legend(); ax.set_aspect("equal")
fig.tight_layout(); fig.savefig(FIG/"map_towers.png", dpi=130); plt.close(fig)

# 2) key feature distributions
feats = ["n_towers","days_since_last_sample","n_violations","reg_age_yrs"]
fig, axs = plt.subplots(2,2, figsize=(10,7))
for axx, c in zip(axs.ravel(), feats):
    d0 = z.loc[z.case==0, c].dropna(); d1 = z.loc[z.case==1, c].dropna()
    axx.hist([d0,d1], bins=15, label=["control","case"], color=["#5B8DEF","#E4572E"], density=True)
    axx.set_title(c); axx.legend()
fig.suptitle("Feature distributions: case vs control (outbreak zone)")
fig.tight_layout(); fig.savefig(FIG/"feature_dists.png", dpi=130); plt.close(fig)

# 3) OR forest plot
fig, ax = plt.subplots(figsize=(8,4.5))
terms = [t for t in tbl.index if t != "const"]
yy = np.arange(len(terms))
ax.errorbar(tbl.loc[terms,"OR"], yy,
            xerr=[tbl.loc[terms,"OR"]-tbl.loc[terms,"CI_low"],
                  tbl.loc[terms,"CI_high"]-tbl.loc[terms,"OR"]],
            fmt="o", color="#333", ecolor="#888", capsize=3)
ax.axvline(1, color="#E4572E", ls="--", lw=1)
ax.set_yticks(yy); ax.set_yticklabels(terms); ax.set_xscale("log")
ax.set_xlabel("odds ratio (log scale)"); ax.set_title("Adjusted odds ratios (95% CI)")
fig.tight_layout(); fig.savefig(FIG/"odds_ratios.png", dpi=130); plt.close(fig)

# save model table + stats
tbl.round(4).to_csv(REP/"odds_ratios.csv")
(REP/"stats.txt").write_text(OUT.getvalue())
log("\nwrote reports/stats.txt, reports/odds_ratios.csv, reports/figures/*.png")
