import sys
from pathlib import Path

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Make "from data_loader import ..." work whether this module is run directly
# from src/analysis/ or imported as src.analysis.analysis_rq5 from the website.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from data_loader import build_master_df, add_spike_flags, compute_returns

# ── display constants ─────────────────────────────────────────────────────────
ASSET_COLORS = {
    "bitcoin":    "#F7931A",
    "gold":       "#D4AF37",
    "msci_world": "#003087",
}
CATEGORY_LABELS = {
    "trade_policy":      "Trade Policy",
    "geopolitics":       "Geopolitics",
    "domestic_politics": "Domestic Politics",
}

# ── RQ5: threshold analysis ───────────────────────────────────────────────────
# Core idea: bin days by article count, compute average price return per bin,
# find the bin where returns first consistently exceed the movement threshold.
# Think of it like a volume dial – we turn it up and watch when the market
# starts to noticeably react.

def run_rq5(
    start_date:         str            = "2025-01-20",
    end_date:           str            = None,
    return_window:      int            = 3,
    movement_threshold: float          = 1.0,   # minimum % return to count as "measurable"
    n_bins:             int            = 5,      # how many article-count bins to create
    df:                 pd.DataFrame   = None,   # pass pre-loaded df to skip raw-data reload
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
    if df is None:
        df = build_master_df(start_date=start_date, end_date=end_date, return_window=return_window)
    else:
        df = df.copy()

    # ensure return columns for the requested window exist
    assets = ["bitcoin", "gold", "msci_world"]
    for asset in assets:
        col = f"{asset}_return_{return_window}d"
        if col not in df.columns:
            prices = df[[f"{a}_close" for a in assets]].rename(
                columns={f"{a}_close": a for a in assets}
            )
            rets = compute_returns(prices, window=return_window)
            df = df.join(rets, how="left")
            break  # all return cols added in one call

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


# ── plotly figures for web app ────────────────────────────────────────────────

def fig_rq5_bins(
    df:                 pd.DataFrame,
    category:           str   = "trade_policy",
    return_window:      int   = 3,
    movement_threshold: float = 1.0,
    n_bins:             int   = 5,
) -> go.Figure:
    """
    Dual-panel figure for RQ5.

    Top panel  : average n-day return per article-count bin (one bar group per asset).
    Bottom panel: % of days in each bin where |return| > movement_threshold.
    The dashed red line at 50 % marks the point where more than half of days
    show a "measurable" market move — the x-position of that crossing is the threshold.

    Parameters
    ----------
    df                 : pre-loaded master DataFrame (output of load_master_from_processed)
    category           : which news category to analyse
    return_window      : forward return window in trading days
    movement_threshold : minimum absolute % return to count as measurable
    n_bins             : number of quantile-based article-count bins
    """
    assets = ["bitcoin", "gold", "msci_world"]
    df = df.copy()

    # ensure return columns exist for the requested window
    for asset in assets:
        if f"{asset}_return_{return_window}d" not in df.columns:
            prices = df[[f"{a}_close" for a in assets]].rename(
                columns={f"{a}_close": a for a in assets}
            )
            df = df.join(compute_returns(prices, window=return_window), how="left")
            break

    return_cols = [f"{a}_return_{return_window}d" for a in assets]

    df[f"{category}_bin"] = pd.qcut(df[category], q=n_bins, duplicates="drop")

    bin_stats = df.groupby(f"{category}_bin", observed=True)[return_cols].agg(
        ["mean", lambda x: (x.abs() > movement_threshold).mean() * 100]
    )
    bin_stats.columns = [
        f"{col}_{stat}"
        for col in return_cols
        for stat in ["avg_return", "pct_exceed"]
    ]
    bin_labels = [f"{b.left:.0f}–{b.right:.0f}" for b in bin_stats.index]

    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=[
            f"Average {return_window}-day return per article-count bin (%)",
            f"% of days with |return| > {movement_threshold}%",
        ],
        vertical_spacing=0.18,
        shared_xaxes=True,
    )

    for asset in assets:
        label = asset.replace("_", " ").title()
        color = ASSET_COLORS[asset]
        avg_col = f"{asset}_return_{return_window}d_avg_return"
        pct_col = f"{asset}_return_{return_window}d_pct_exceed"

        fig.add_trace(go.Bar(
            x=bin_labels, y=bin_stats[avg_col].round(3),
            name=label, marker_color=color, showlegend=True,
        ), row=1, col=1)

        fig.add_trace(go.Bar(
            x=bin_labels, y=bin_stats[pct_col].round(1),
            name=label, marker_color=color, showlegend=False,
        ), row=2, col=1)

    # reference line: 50 % is where ">half the days show measurable movement"
    fig.add_hline(
        y=50, line_dash="dash", line_color="red", line_width=1.5,
        annotation_text="50 % mark", annotation_position="top right",
        row=2, col=1,
    )

    cat_label = CATEGORY_LABELS.get(category, category)
    fig.update_layout(
        title=f"RQ5 — {cat_label}: article volume vs. market reaction",
        barmode="group",
        legend=dict(orientation="h", yanchor="top", y=-0.12, x=0.5, xanchor="center"),
        plot_bgcolor="#f8f9fa",
        paper_bgcolor="white",
        height=560,
        margin=dict(t=70, b=70, l=60, r=30),
    )
    fig.update_xaxes(title_text="Daily article count (articles / day)", row=2, col=1)
    fig.update_yaxes(title_text="Avg return (%)", row=1, col=1)
    fig.update_yaxes(title_text="Days exceeding threshold (%)", row=2, col=1)
    return fig


def fig_rq5_threshold_summary(
    df:                 pd.DataFrame,
    return_window:      int   = 3,
    movement_threshold: float = 1.0,
    n_bins:             int   = 5,
) -> go.Figure:
    """
    Horizontal bar chart showing the estimated article-count threshold per category —
    the lower bound of the first bin where >50 % of days show a measurable return.
    A None threshold (no bin reached the 50 % mark) is shown as 'n/a'.
    """
    results = run_rq5(df=df, return_window=return_window,
                      movement_threshold=movement_threshold, n_bins=n_bins)

    categories = list(results.keys())
    thresholds = [results[c]["threshold"] for c in categories]
    labels     = [CATEGORY_LABELS.get(c, c) for c in categories]
    values     = [t if t is not None else 0 for t in thresholds]
    texts      = [f"{t:.0f} articles/day" if t is not None else "n/a" for t in thresholds]

    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation="h",
        text=texts,
        textposition="outside",
        marker_color=["#003087", "#D4AF37", "#F7931A"],
    ))
    fig.update_layout(
        title="Estimated article-count threshold per news category",
        xaxis_title="Articles / day",
        plot_bgcolor="#f8f9fa",
        paper_bgcolor="white",
        height=280,
        margin=dict(t=50, b=40, l=160, r=80),
    )
    return fig


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