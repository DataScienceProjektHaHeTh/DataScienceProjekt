"""
rq1_correlation.py
==================
RQ1: To what extent does the daily frequency of Trump-related news coverage
in the Guardian, categorized by topic, correlate with cumulative 3-day price
return of MSCI World, Gold, and Bitcoin following a coverage spike?

Method (from Methods file — Group 1: Correlation Analysis):
  - Filter the full timeline to spike days per category
  - For each of the 9 category x asset pairs, compute Spearman correlation
    between article count on spike days and the 3-day return starting that day
  - Spearman is preferred over Pearson because article counts and returns are
    not normally distributed

Output:
  data/processed/rq1_correlations.csv   — 3x3 correlation matrix
  data/processed/rq1_pvalues.csv        — 3x3 p-value matrix
  Printed report with significance stars and observation counts
"""

import pandas as pd
from scipy import stats
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"

CATEGORIES   = ["trade_policy", "geopolitics", "domestic_politics"]
ASSETS       = ["msci_world", "gold", "bitcoin"]
CAT_LABELS   = {
    "trade_policy":      "Trade Policy",
    "geopolitics":       "Geopolitics",
    "domestic_politics": "Domestic Politics",
}
ASSET_LABELS = {
    "msci_world": "MSCI World",
    "gold":       "Gold",
    "bitcoin":    "Bitcoin",
}


# ── Core computation ───────────────────────────────────────────────────────────

def compute_correlations(
    master: pd.DataFrame,
    method: str = "spearman",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Compute correlation between article count and 3-day return for every
    category × asset pair, restricted to spike days.

    Parameters
    ----------
    master : pd.DataFrame
        The master DataFrame from data_prep (must contain spike flag columns).
    method : str
        'spearman' (default) or 'pearson'. Spearman is robust to non-normal
        distributions; Pearson assumes linearity and normality. Exposing this
        lets the website dropdown switch between them interactively.

    Steps per pair:
      1. Filter master to rows where the category spike flag is True
      2. Select the article count column and the asset return column
      3. Drop rows where either is NaN (e.g. spike day falls on a market holiday)
      4. Compute the chosen correlation and its two-sided p-value

    Returns three 3x3 DataFrames (rows=categories, cols=assets):
      correlations — r coefficients
      pvalues      — two-sided p-values
      n_obs        — number of valid observations used for each pair
    """
    correlations = pd.DataFrame(index=CATEGORIES, columns=ASSETS, dtype=float)
    pvalues      = pd.DataFrame(index=CATEGORIES, columns=ASSETS, dtype=float)
    n_obs        = pd.DataFrame(index=CATEGORIES, columns=ASSETS, dtype=int)

    for cat in CATEGORIES:
        spike_days = master[master[f"{cat}_spike"]]

        for asset in ASSETS:
            pair = spike_days[[f"{cat}_count", f"{asset}_3d_return"]].dropna()
            n = len(pair)
            n_obs.loc[cat, asset] = n

            if n < 3:
                correlations.loc[cat, asset] = float("nan")
                pvalues.loc[cat, asset]      = float("nan")
                continue

            x = pair[f"{cat}_count"]
            y = pair[f"{asset}_3d_return"]
            if method == "pearson":
                r, p = stats.pearsonr(x, y)
            else:
                r, p = stats.spearmanr(x, y)

            correlations.loc[cat, asset] = round(r, 4)
            pvalues.loc[cat, asset]      = round(p, 4)

    return correlations, pvalues, n_obs


# ── Reporting ──────────────────────────────────────────────────────────────────

def significance_star(p: float) -> str:
    if pd.isna(p):
        return ""
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    if p < 0.10:
        return "."
    return ""


def print_report(correlations: pd.DataFrame, pvalues: pd.DataFrame, n_obs: pd.DataFrame) -> None:
    print("\n" + "=" * 65)
    print("RQ1 — Spearman Correlation: Article Count vs 3-Day Return")
    print("       (filtered to spike days per category)")
    print("=" * 65)

    header = f"{'Category':<22}" + "".join(f"{ASSET_LABELS[a]:>14}" for a in ASSETS)
    print(header)
    print("-" * 65)

    for cat in CATEGORIES:
        label = CAT_LABELS[cat]
        row_corr = ""
        row_n    = ""
        for asset in ASSETS:
            r  = correlations.loc[cat, asset]
            p  = pvalues.loc[cat, asset]
            n  = n_obs.loc[cat, asset]
            star = significance_star(p)
            if pd.isna(r):
                row_corr += f"{'—':>14}"
            else:
                row_corr += f"{r:+.4f}{star:>3}".rjust(14)
            row_n += f"(n={n})".rjust(14)

        print(f"{label:<22}{row_corr}")
        print(f"{'':22}{row_n}")

    print("-" * 65)
    print("Significance: *** p<0.001  ** p<0.01  * p<0.05  . p<0.10")
    print()

    # Spike day summary
    print("Spike day counts per category:")
    for cat in CATEGORIES:
        n_spikes = master[master[f"{cat}_spike"]].shape[0]
        print(f"  {CAT_LABELS[cat]:<22}: {n_spikes} spike days")
    print()


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    master = pd.read_csv(PROC / "master.csv", index_col="date", parse_dates=True)

    correlations, pvalues, n_obs = compute_correlations(master)

    print_report(correlations, pvalues, n_obs)

    # Save results
    correlations.rename(index=CAT_LABELS, columns=ASSET_LABELS).to_csv(PROC / "rq1_correlations.csv")
    pvalues.rename(index=CAT_LABELS, columns=ASSET_LABELS).to_csv(PROC / "rq1_pvalues.csv")
    print("Saved: rq1_correlations.csv, rq1_pvalues.csv")
