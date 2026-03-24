"""
rq3_sentiment.py
================
RQ3: How does the average daily sentiment score of Trump-related Guardian
articles within each news category relate to the direction and magnitude
of the cumulative 3-day price return across all three asset classes?

Method (from Methods file — Group 3: Sentiment Scoring and Correlation):
  - Use the VADER compound scores already computed by sentiment.py and
    aggregated per day per category in data_prep.py
  - For each of the 9 category × asset pairs, compute Spearman correlation
    between the daily average sentiment and the 3-day return
  - Spearman is used because sentiment scores are bounded [-1, 1] and
    returns are not normally distributed
  - Results reveal whether negative news reliably drives negative returns,
    or whether some assets show a flight-to-safety or contrarian pattern

Output:
  data/processed/rq3_correlations.csv   — 3x3 correlation matrix
  data/processed/rq3_pvalues.csv        — 3x3 p-value matrix
  Printed report with significance stars and direction interpretation
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

def compute_sentiment_correlations(
    master: pd.DataFrame,
    method: str = "spearman",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Compute correlation between daily average sentiment score and 3-day return
    for every category × asset pair, using ALL days (not just spike days).

    Parameters
    ----------
    master : pd.DataFrame
        Master DataFrame from data_prep (must contain *_sentiment columns).
    method : str
        'spearman' (default) or 'pearson'. Exposed for website dropdown.

    Unlike RQ1 (which restricts to spike days), RQ3 uses the full date range
    because sentiment varies every day, not only on high-volume days.

    Returns three 3x3 DataFrames (rows=categories, cols=assets):
      correlations — r coefficients
      pvalues      — two-sided p-values
      n_obs        — number of valid observations used for each pair
    """
    correlations = pd.DataFrame(index=CATEGORIES, columns=ASSETS, dtype=float)
    pvalues      = pd.DataFrame(index=CATEGORIES, columns=ASSETS, dtype=float)
    n_obs        = pd.DataFrame(index=CATEGORIES, columns=ASSETS, dtype=int)

    for cat in CATEGORIES:
        for asset in ASSETS:
            pair = master[[f"{cat}_sentiment", f"{asset}_3d_return"]].dropna()
            n = len(pair)
            n_obs.loc[cat, asset] = n

            if n < 3:
                correlations.loc[cat, asset] = float("nan")
                pvalues.loc[cat, asset]      = float("nan")
                continue

            x = pair[f"{cat}_sentiment"]
            y = pair[f"{asset}_3d_return"]
            if method == "pearson":
                r, p = stats.pearsonr(x, y)
            else:
                r, p = stats.spearmanr(x, y)

            correlations.loc[cat, asset] = round(r, 4)
            pvalues.loc[cat, asset]      = round(p, 4)

    return correlations, pvalues, n_obs


# ── Sentiment bucketing ────────────────────────────────────────────────────────

def compute_sentiment_buckets(
    master: pd.DataFrame,
    negative_threshold: float = -0.05,
    positive_threshold: float = 0.05,
) -> dict[str, pd.DataFrame]:
    """
    Split days into negative / neutral / positive sentiment buckets and compute
    the average 3-day return per asset within each bucket.

    This answers the "direction and magnitude" part of RQ3 more directly than
    a single correlation coefficient: it shows whether days with clearly negative
    news actually lead to negative returns, and by how much.

    VADER standard thresholds (also used in sentiment.py):
      compound >= 0.05  → positive
      compound <= -0.05 → negative
      otherwise         → neutral
    The thresholds are exposed as parameters so the website slider can adjust them.

    Returns a dict mapping category name → DataFrame with:
      columns = [negative, neutral, positive]
      rows    = assets
      values  = mean 3-day return (%) and count n within that bucket
    """
    results = {}
    for cat in CATEGORIES:
        sentiment_col = f"{cat}_sentiment"
        rows = []
        for asset in ASSETS:
            pair = master[[sentiment_col, f"{asset}_3d_return"]].dropna()

            neg  = pair[pair[sentiment_col] <= negative_threshold][f"{asset}_3d_return"]
            neu  = pair[(pair[sentiment_col] > negative_threshold) & (pair[sentiment_col] < positive_threshold)][f"{asset}_3d_return"]
            pos  = pair[pair[sentiment_col] >= positive_threshold][f"{asset}_3d_return"]

            rows.append({
                "asset":              ASSET_LABELS[asset],
                "negative_mean":      round(neg.mean(), 4) if len(neg) > 0 else float("nan"),
                "negative_n":         len(neg),
                "neutral_mean":       round(neu.mean(), 4) if len(neu) > 0 else float("nan"),
                "neutral_n":          len(neu),
                "positive_mean":      round(pos.mean(), 4) if len(pos) > 0 else float("nan"),
                "positive_n":         len(pos),
            })

        results[cat] = pd.DataFrame(rows).set_index("asset")
    return results


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


def interpret_direction(r: float) -> str:
    """
    Return a short label describing what the sign of r means in context.
    Positive r: more positive sentiment → higher 3-day return (aligned)
    Negative r: more positive sentiment → lower 3-day return (contrarian)
    """
    if pd.isna(r):
        return "—"
    if abs(r) < 0.05:
        return "flat"
    return "aligned" if r > 0 else "contrarian"


def print_report(
    correlations: pd.DataFrame,
    pvalues: pd.DataFrame,
    n_obs: pd.DataFrame,
) -> None:
    print("\n" + "=" * 70)
    print("RQ3 — Spearman Correlation: Daily Sentiment vs 3-Day Return")
    print("       (all days with available sentiment and return data)")
    print("=" * 70)

    header = f"{'Category':<22}" + "".join(f"{ASSET_LABELS[a]:>16}" for a in ASSETS)
    print(header)
    print("-" * 70)

    for cat in CATEGORIES:
        label = CAT_LABELS[cat]
        row_corr = ""
        row_n    = ""
        row_dir  = ""
        for asset in ASSETS:
            r    = correlations.loc[cat, asset]
            p    = pvalues.loc[cat, asset]
            n    = n_obs.loc[cat, asset]
            star = significance_star(p)
            direction = interpret_direction(r)
            if pd.isna(r):
                row_corr += f"{'—':>16}"
                row_dir  += f"{'—':>16}"
            else:
                row_corr += f"{r:+.4f}{star:>3}".rjust(16)
                row_dir  += f"({direction})".rjust(16)
            row_n += f"(n={n})".rjust(16)

        print(f"{label:<22}{row_corr}")
        print(f"{'':22}{row_n}")
        print(f"{'':22}{row_dir}")
        print()

    print("-" * 70)
    print("Significance: *** p<0.001  ** p<0.01  * p<0.05  . p<0.10")
    print()
    print("Direction key:")
    print("  aligned    → positive sentiment correlates with positive returns")
    print("  contrarian → positive sentiment correlates with negative returns")
    print("               (could indicate a 'buy the rumor, sell the news' effect")
    print("                or flight-to-safety into Gold/BTC on negative news)")
    print("  flat       → correlation near zero, no meaningful direction")
    print()

    # Sentiment summary statistics
    print("Daily sentiment averages by category (VADER compound, range -1 to +1):")
    for cat in CATEGORIES:
        col = f"{cat}_sentiment"
        if col in master.columns:
            mean = master[col].mean()
            std  = master[col].std()
            print(f"  {CAT_LABELS[cat]:<22}: mean={mean:+.4f}, std={std:.4f}")
    print()


# ── Entry point ────────────────────────────────────────────────────────────────

def print_bucket_report(buckets: dict) -> None:
    print("\n" + "=" * 72)
    print("RQ3 — Average 3-Day Return by Sentiment Bucket")
    print("      (negative: compound ≤ -0.05 | neutral: -0.05 to +0.05 | positive: ≥ +0.05)")
    print("=" * 72)

    for cat, df in buckets.items():
        print(f"\n  Category: {CAT_LABELS[cat]}")
        print(f"  {'Asset':<14} {'Negative':>14} {'Neutral':>14} {'Positive':>14}")
        print(f"  {'-'*12:<14} {'-'*12:>14} {'-'*12:>14} {'-'*12:>14}")
        for asset, row in df.iterrows():
            neg_str = f"{row['negative_mean']:+.2f}% (n={int(row['negative_n'])})"  if not pd.isna(row['negative_mean']) else "—"
            neu_str = f"{row['neutral_mean']:+.2f}% (n={int(row['neutral_n'])})"    if not pd.isna(row['neutral_mean'])  else "—"
            pos_str = f"{row['positive_mean']:+.2f}% (n={int(row['positive_n'])})"  if not pd.isna(row['positive_mean']) else "—"
            print(f"  {asset:<14} {neg_str:>14} {neu_str:>14} {pos_str:>14}")
    print()


if __name__ == "__main__":
    master = pd.read_csv(PROC / "master.csv", index_col="date", parse_dates=True)

    sentiment_cols = [f"{cat}_sentiment" for cat in CATEGORIES]
    missing = [c for c in sentiment_cols if c not in master.columns]
    if missing:
        print(f"[ERROR] Missing sentiment columns: {missing}")
        print("Run sentiment.py and then data_prep.py first.")
        raise SystemExit(1)

    correlations, pvalues, n_obs = compute_sentiment_correlations(master)
    print_report(correlations, pvalues, n_obs)

    buckets = compute_sentiment_buckets(master)
    print_bucket_report(buckets)

    correlations.rename(index=CAT_LABELS, columns=ASSET_LABELS).to_csv(PROC / "rq3_correlations.csv")
    pvalues.rename(index=CAT_LABELS, columns=ASSET_LABELS).to_csv(PROC / "rq3_pvalues.csv")
    print("Saved: rq3_correlations.csv, rq3_pvalues.csv")
