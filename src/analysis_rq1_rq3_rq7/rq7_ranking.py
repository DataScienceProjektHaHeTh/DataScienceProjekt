"""
rq7_ranking.py
==============
RQ7: Which of the three news categories generates the highest average daily
article volume, and how does the ranking by coverage volume compare to the
ranking by strength of correlation with cumulative 3-day price returns?

Method (from Methods file — Group 1: Correlation Analysis):
  - Compute mean daily article count per category → volume ranking
  - Load the RQ1 Spearman correlations → correlation ranking
  - Average correlation strength across all three assets per category
    (using absolute values so direction doesn't cancel out)
  - Compare both rankings side by side

Output:
  data/processed/rq7_rankings.csv   — combined ranking table
  Printed report comparing the two rankings
"""

import pandas as pd
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


# ── Step 1: Volume ranking ─────────────────────────────────────────────────────

def compute_volume_ranking(master: pd.DataFrame) -> pd.DataFrame:
    """
    Compute average daily article count per category over the full date range.
    Ranks categories from 1 (highest volume) to 3 (lowest volume).
    """
    means = {}
    for cat in CATEGORIES:
        means[CAT_LABELS[cat]] = master[f"{cat}_count"].mean()

    volume = pd.Series(means, name="avg_daily_articles").round(2)
    volume_rank = volume.rank(ascending=False).astype(int).rename("volume_rank")

    return pd.concat([volume, volume_rank], axis=1).sort_values("volume_rank")


# ── Step 2: Correlation ranking ────────────────────────────────────────────────

def compute_correlation_ranking() -> pd.DataFrame:
    """
    Load the RQ1 Spearman correlation results and summarise them into a single
    correlation strength value per category.

    Strategy: take the mean of the absolute correlation coefficients across
    all three assets. Absolute value is used because the question asks about
    *strength* of correlation, not direction — a strong negative correlation
    is still a strong market signal.
    """
    corr_df = pd.read_csv(PROC / "rq1_correlations.csv", index_col=0)

    # Mean absolute correlation across all three assets for each category
    mean_abs_corr = corr_df.abs().mean(axis=1).round(4).rename("mean_abs_correlation")
    corr_rank = mean_abs_corr.rank(ascending=False).astype(int).rename("correlation_rank")

    # Also keep per-asset correlations for the detailed view
    detail = pd.concat([corr_df, mean_abs_corr, corr_rank], axis=1).sort_values("correlation_rank")
    return detail


# ── Step 3: Combine and compare ────────────────────────────────────────────────

def compare_rankings(volume_df: pd.DataFrame, corr_df: pd.DataFrame) -> pd.DataFrame:
    """
    Join volume ranking and correlation ranking on category name.
    Highlights mismatches between the two rankings.
    """
    combined = volume_df.join(corr_df[["mean_abs_correlation", "correlation_rank"]])
    combined["rank_mismatch"] = (combined["volume_rank"] != combined["correlation_rank"])
    return combined


# ── Reporting ──────────────────────────────────────────────────────────────────

def print_report(volume_df: pd.DataFrame, corr_df: pd.DataFrame, combined: pd.DataFrame) -> None:
    print("\n" + "=" * 60)
    print("RQ7 — Volume Ranking vs Correlation Ranking")
    print("=" * 60)

    print("\nPart A — Average daily article volume per category:")
    print("-" * 45)
    print(f"  {'Rank':<6} {'Category':<22} {'Avg articles/day':>16}")
    print(f"  {'-'*4:<6} {'-'*20:<22} {'-'*15:>16}")
    for _, row in volume_df.iterrows():
        print(f"  #{int(row['volume_rank'])}     {row.name:<22} {row['avg_daily_articles']:>16.2f}")

    print("\nPart B — Correlation strength per category (mean |r| across assets):")
    print("-" * 60)
    print(f"  {'Rank':<6} {'Category':<22} {'Mean |r|':>10}", end="")
    for asset in ASSET_LABELS.values():
        print(f"  {asset:>12}", end="")
    print()
    print(f"  {'-'*4:<6} {'-'*20:<22} {'-'*8:>10}", end="")
    for _ in ASSET_LABELS:
        print(f"  {'-'*10:>12}", end="")
    print()
    for _, row in corr_df.sort_values("correlation_rank").iterrows():
        print(f"  #{int(row['correlation_rank'])}     {row.name:<22} {row['mean_abs_correlation']:>10.4f}", end="")
        for asset in ASSET_LABELS.values():
            val = row.get(asset, float("nan"))
            print(f"  {val:>+12.4f}", end="")
        print()

    print("\nPart C — Ranking comparison:")
    print("-" * 55)
    print(f"  {'Category':<22} {'Vol rank':>10} {'Corr rank':>10} {'Match?':>8}")
    print(f"  {'-'*20:<22} {'-'*8:>10} {'-'*8:>10} {'-'*6:>8}")
    for _, row in combined.iterrows():
        match = "YES" if not row["rank_mismatch"] else "NO ←"
        print(f"  {row.name:<22} #{int(row['volume_rank']):>8} #{int(row['correlation_rank']):>8} {match:>8}")

    mismatches = combined["rank_mismatch"].sum()
    print()
    if mismatches == 0:
        print("  → Volume ranking and correlation ranking are identical.")
    else:
        print(f"  → {mismatches} category/categories have mismatched rankings.")
        print("    This means covering more does NOT necessarily mean moving markets more.")
    print()


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    master = pd.read_csv(PROC / "master.csv", index_col="date", parse_dates=True)

    volume_df  = compute_volume_ranking(master)
    corr_df    = compute_correlation_ranking()
    combined   = compare_rankings(volume_df, corr_df)

    print_report(volume_df, corr_df, combined)

    combined.to_csv(PROC / "rq7_rankings.csv")
    print("Saved: rq7_rankings.csv")
