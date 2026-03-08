import pandas as pd
import numpy as np
from data_loader import build_master_df, add_spike_flags

# ── RQ5: threshold analysis ───────────────────────────────────────────────────
# Core idea: bin days by article count, compute average price return per bin,
# find the bin where returns first consistently exceed the movement threshold.
# Think of it like a volume dial – we turn it up and watch when the market
# starts to noticeably react.

def run_rq5(
    start_date:       str   = "2025-01-20",
    end_date:         str   = None,
    return_window:    int   = 3,
    movement_threshold: float = 1.0,   # minimum % return to count as "measurable"
    n_bins:           int   = 5,       # how many article-count bins to create
) -> dict:
    """
    RQ5: Above which daily article volume threshold per news category does a
    measurable cumulative 3-day price return exceeding 1% first consistently
    appear across MSCI World, Gold, and Bitcoin?

    Parameters
    ----------
    start_date         : start of analysis window
    end_date           : end of analysis window (None = all available data)
    return_window      : forward return window in trading days (default 3)
    movement_threshold : minimum absolute % return to count as measurable (default 1.0)
    n_bins             : number of article count bins (default 5)

    Returns
    -------
    dict with keys per category, each containing:
        - bin_summary : DataFrame with bin ranges, avg returns, % days exceeding threshold
        - threshold   : estimated article count threshold per asset
    """
    df = build_master_df(start_date=start_date, end_date=end_date, return_window=return_window)

    categories   = ["trade_policy", "geopolitics", "domestic_politics"]
    assets       = ["bitcoin", "gold", "msci_world"]
    return_cols  = [f"{a}_return_{return_window}d" for a in assets]

    results = {}

    for cat in categories:
        # create equal-frequency bins (quantile-based) so each bin has similar
        # number of observations – avoids empty bins on sparse data
        df[f"{cat}_bin"] = pd.qcut(
            df[cat],
            q=n_bins,
            duplicates="drop",   # handles ties in low-count days
        )

        # for each bin compute:
        # 1. average return per asset
        # 2. % of days where abs(return) > movement_threshold (= "measurable movement")
        bin_summary = df.groupby(f"{cat}_bin", observed=True)[return_cols].agg(
            ["mean", lambda x: (x.abs() > movement_threshold).mean() * 100]
        )
        bin_summary.columns = [
            f"{col}_{stat}"
            for col in return_cols
            for stat in ["avg_return", "pct_days_exceeding_threshold"]
        ]

        # estimate threshold: first bin where ALL assets show measurable movement
        # on more than 50% of days
        pct_cols = [c for c in bin_summary.columns if "pct_days_exceeding_threshold" in c]
        bin_summary["all_assets_exceed"] = (bin_summary[pct_cols] > 50).all(axis=1)

        # find the lower bound of the first bin where all assets exceed threshold
        first_threshold_bin = bin_summary[bin_summary["all_assets_exceed"]].index
        threshold_value = (
            first_threshold_bin[0].left   # lower bound of the bin interval
            if len(first_threshold_bin) > 0
            else None  # no threshold found in the data
        )

        results[cat] = {
            "bin_summary":  bin_summary,
            "threshold":    threshold_value,
            "bin_col":      f"{cat}_bin",
        }

        print(f"\n── {cat.upper()} ──")
        print(f"   Estimated threshold: {threshold_value} articles/day")
        print(bin_summary[[c for c in bin_summary.columns if "pct_days" in c]].round(1))

    return results


# ── helper: summary table for web app ────────────────────────────────────────
def get_threshold_summary(results: dict) -> pd.DataFrame:
    """
    Returns a clean summary table of estimated thresholds per category
    for display in the web application.
    """
    rows = []
    for cat, data in results.items():
        rows.append({
            "category":  cat.replace("_", " ").title(),
            "threshold": data["threshold"],
        })
    return pd.DataFrame(rows)

if __name__ == "__main__":
    results = run_rq5(start_date="2025-01-20")
    print(get_threshold_summary(results))