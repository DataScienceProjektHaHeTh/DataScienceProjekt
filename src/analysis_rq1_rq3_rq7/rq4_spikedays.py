# RQ4: To what degree does the co-occurrence of spikes across multiple news categories
# amplify the cumulative price return compared to single-category spikes?
#
# Charts:
#   build_chart_rq4                  → Dot Plot with confidence intervals
#                                      (mean abnormal return per asset, single vs multi)
#   build_chart_rq4_category_breakdown → Parallel Coordinates Plot
#                                        (each spike event = one line across Gold/Bitcoin/MSCI axes)

import pandas as pd
import numpy as np
import os
import sys
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rq2_spikedays import (
    get_spike_days_of_single_class,
    get_shared_spike_days,
    calculate_price_return,
    all_daily_closes,
    counts_df,
    CATEGORY_COLUMNS,
    ASSET_LABELS,
)

# RQ4 reuses all_daily_closes from RQ2 under the name all_daily_returns
all_daily_returns = all_daily_closes

# ── Rebuild per-category spike days ──────────────────────────────────────────
single_category_spike_days = [
    (label, get_spike_days_of_single_class(counts_df, col))
    for label, col in CATEGORY_COLUMNS.items()
]

shared_spike_days = get_shared_spike_days([s for _, s in single_category_spike_days])


def get_isolated_spike_days(all_spike_days):
    """Find days that spike in EXACTLY ONE category."""
    all_dates = []
    for _, spike_days in all_spike_days:
        all_dates.extend(spike_days.index.tolist())
    date_counts = Counter(all_dates)
    return sorted([date for date, count in date_counts.items() if count == 1])


isolated_spike_days = get_isolated_spike_days(single_category_spike_days)

# ── Date → category set lookup ────────────────────────────────────────────────
date_to_categories = {}
for label, spike_days in single_category_spike_days:
    for date in spike_days.index:
        date_to_categories.setdefault(date, set()).add(label)

# ── Module-level summary ──────────────────────────────────────────────────────
DAYS_AFTER = 3
results = []
for asset_name, price_data in all_daily_returns.items():
    multi  = calculate_price_return(shared_spike_days,   price_data, DAYS_AFTER)
    multi["spike_type"] = "multi-category"
    multi["asset"]      = asset_name
    single = calculate_price_return(isolated_spike_days, price_data, DAYS_AFTER)
    single["spike_type"] = "single-category"
    single["asset"]      = asset_name
    results.extend([multi, single])

df_all = pd.concat(results, ignore_index=True)
summary = df_all.groupby(["asset", "spike_type"])["abnormal_return_%"].agg(
    avg_return="mean", median_return="median", std_return="std", count="count"
).reset_index()


# ── Chart colours ─────────────────────────────────────────────────────────────
SPIKE_COLORS = {
    "multi-category":  "#c0392b",   # deep red
    "single-category": "#2980b9",   # steel blue
}
ASSET_COLORS = {
    "gold_close":       "#F5C518",
    "bitcoin_close":    "#4A90D9",
    "msci_world_close": "#27AE60",
}


# ─────────────────────────────────────────────────────────────────────────────
#  CHART 1 — Dot Plot with 95 % confidence intervals
#  Replaces: grouped bar chart
#
#  Each dot = mean abnormal return for one (asset, spike_type) pair.
#  Error bars = ±1.96 × SE  (95 % CI).
#  Filled dot  = multi-category spike
#  Open dot    = single-category spike
# ─────────────────────────────────────────────────────────────────────────────

def build_chart_rq4(days_after):
    """Dot plot: mean abnormal return ± 95% CI, single vs multi-category spikes."""
    res = []
    for asset_name, price_data in all_daily_returns.items():
        for spike_type, spike_days in [
            ("multi-category",  shared_spike_days),
            ("single-category", isolated_spike_days),
        ]:
            df = calculate_price_return(spike_days, price_data, days_after)
            if df.empty:
                continue
            vals = df["abnormal_return_%"]
            n    = len(vals)
            mean = vals.mean()
            se   = vals.std() / np.sqrt(n) if n > 1 else 0
            ci   = 1.96 * se
            res.append({
                "asset":      asset_name,
                "label":      ASSET_LABELS.get(asset_name, asset_name),
                "spike_type": spike_type,
                "mean":       round(mean, 3),
                "ci":         round(ci,   3),
                "n":          n,
            })

    df_plot = pd.DataFrame(res)
    fig     = go.Figure()

    for spike_type, marker_symbol, fill in [
        ("multi-category",  "circle",      SPIKE_COLORS["multi-category"]),
        ("single-category", "circle-open", SPIKE_COLORS["single-category"]),
    ]:
        sub = df_plot[df_plot["spike_type"] == spike_type]
        fig.add_trace(go.Scatter(
            name=spike_type,
            x=sub["label"],
            y=sub["mean"],
            mode="markers",
            marker=dict(
                symbol=marker_symbol,
                size=14,
                color=fill,
                line=dict(color=fill, width=2),
            ),
            error_y=dict(
                type="data",
                array=sub["ci"].tolist(),
                visible=True,
                color=fill,
                thickness=2,
                width=6,
            ),
            customdata=sub[["ci", "n"]].values,
            hovertemplate=(
                "<b>%{x}</b><br>"
                f"Spike type: {spike_type}<br>"
                "Mean abnormal return: <b>%{y:.2f}%</b><br>"
                "95% CI: ±%{customdata[0]:.2f}%<br>"
                "Events: %{customdata[1]}"
                "<extra></extra>"
            ),
        ))

    fig.add_hline(y=0, line_dash="dash", line_color="black", line_width=1)

    fig.update_layout(
        title=(
            f"RQ4: Mean Abnormal Return — Single vs Multi-Category Spikes "
            f"({days_after}-day window)<br>"
            "<sup>Error bars = 95% confidence interval &nbsp;·&nbsp; "
            "Filled = multi-category &nbsp;·&nbsp; Open = single-category</sup>"
        ),
        xaxis_title="Asset",
        yaxis_title="Mean Abnormal Return (%)",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=480,
        hovermode="x unified",
        legend=dict(orientation="h", y=-0.15),
        xaxis=dict(showgrid=True, gridcolor="#eee"),
        yaxis=dict(showgrid=True, gridcolor="#eee", zeroline=False),
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
#  CHART 2 — Small Multiples Scatter
#  3 subplots showing every pair of assets:
#    Gold vs Bitcoin  |  Gold vs MSCI World  |  Bitcoin vs MSCI World
#  Each dot = one spike event, coloured by number of spiking categories.
#  A diagonal reference line (y=x) shows symmetric co-movement.
#  `asset_name` param kept for API compatibility — chart always shows all assets.
# ─────────────────────────────────────────────────────────────────────────────

def build_chart_rq4_category_breakdown(asset_name, days_after):
    """
    Small multiples scatter: 3 subplots, one per asset pair.
    Each dot = one spike event. Colour = number of spiking categories.
    Shows whether assets move together or diverge on the same events.
    """
    assets = list(all_daily_returns.keys())

    # ── Collect per-event returns for every asset ────────────────────────────
    event_returns = {}   # date_str → {asset: abnormal_return_%}
    all_spike_dates = sorted(set(isolated_spike_days) | set(shared_spike_days))

    for asset, price_data in all_daily_returns.items():
        df = calculate_price_return(all_spike_dates, price_data, days_after)
        for _, row in df.iterrows():
            event_returns.setdefault(row["date"], {})[asset] = row["abnormal_return_%"]

    # Keep only events where all assets have data
    rows = []
    for date_str, asset_vals in event_returns.items():
        if not all(a in asset_vals for a in assets):
            continue
        date   = pd.to_datetime(date_str)
        n_cats = len(date_to_categories.get(date, set()))
        rows.append({
            "date":   date_str,
            "n_cats": n_cats,
            **{a: asset_vals[a] for a in assets},
        })

    if not rows:
        return go.Figure()

    df_events = pd.DataFrame(rows)

    # ── Colour map ────────────────────────────────────────────────────────────
    CAT_COLORS = {
        1: "#2980b9",   # single   — blue
        2: "#e67e22",   # partial  — orange
        3: "#c0392b",   # all 3    — red
    }
    CAT_LABELS = {
        1: "Single category",
        2: "Two categories",
        3: "All categories",
    }

    # ── Define the 3 asset pairs ──────────────────────────────────────────────
    pairs = [
        (assets[0], assets[1]),   # Gold vs Bitcoin
        (assets[0], assets[2]),   # Gold vs MSCI World
        (assets[1], assets[2]),   # Bitcoin vs MSCI World
    ]
    pair_titles = [
        f"{ASSET_LABELS.get(a, a)} vs {ASSET_LABELS.get(b, b)}"
        for a, b in pairs
    ]

    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=pair_titles,
        horizontal_spacing=0.10,
    )

    # Track which n_cats values we've already added to the legend
    legend_added = set()

    for col_idx, (asset_x, asset_y) in enumerate(pairs, start=1):
        x_label = ASSET_LABELS.get(asset_x, asset_x)
        y_label = ASSET_LABELS.get(asset_y, asset_y)

        for n_cats in sorted(df_events["n_cats"].unique()):
            sub   = df_events[df_events["n_cats"] == n_cats]
            color = CAT_COLORS.get(n_cats, "#888")
            show_legend = n_cats not in legend_added

            fig.add_trace(
                go.Scatter(
                    name=CAT_LABELS.get(n_cats, f"{n_cats} categories"),
                    x=sub[asset_x],
                    y=sub[asset_y],
                    mode="markers",
                    marker=dict(
                        size=10,
                        color=color,
                        opacity=0.8,
                        line=dict(color="white", width=0.8),
                    ),
                    showlegend=show_legend,
                    legendgroup=str(n_cats),
                    customdata=sub[["date", "n_cats"]].values,
                    hovertemplate=(
                        "<b>%{customdata[0]}</b><br>"
                        f"{x_label}: %{{x:.2f}}%<br>"
                        f"{y_label}: %{{y:.2f}}%<br>"
                        "Spiking categories: %{customdata[1]}"
                        "<extra></extra>"
                    ),
                ),
                row=1, col=col_idx,
            )
            legend_added.add(n_cats)

        # ── Diagonal reference line (y = x) ──────────────────────────────────
        all_vals = pd.concat([df_events[asset_x], df_events[asset_y]])
        axis_min = all_vals.min() - 1
        axis_max = all_vals.max() + 1

        fig.add_trace(
            go.Scatter(
                x=[axis_min, axis_max],
                y=[axis_min, axis_max],
                mode="lines",
                line=dict(color="#bbb", width=1, dash="dot"),
                showlegend=(col_idx == 1),
                name="y = x (equal move)",
                legendgroup="diagonal",
            ),
            row=1, col=col_idx,
        )

        # Zero lines
        fig.add_hline(y=0, line_dash="dash", line_color="#ddd",
                      line_width=1, row=1, col=col_idx)
        fig.add_vline(x=0, line_dash="dash", line_color="#ddd",
                      line_width=1, row=1, col=col_idx)

        fig.update_xaxes(
            title_text=f"{x_label} return (%)",
            showgrid=True, gridcolor="#eee",
            row=1, col=col_idx,
        )
        fig.update_yaxes(
            title_text=f"{y_label} return (%)" if col_idx == 1 else "",
            showgrid=True, gridcolor="#eee",
            row=1, col=col_idx,
        )

    fig.update_layout(
        title=(
            f"RQ4: Asset Return Co-movement on Spike Events ({days_after}-day abnormal return)<br>"
            "<sup>Each dot = one spike event &nbsp;·&nbsp; "
            "Colour = number of spiking categories &nbsp;·&nbsp; "
            "Dotted line = equal movement</sup>"
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=460,
        legend=dict(orientation="h", y=-0.18),
    )
    return fig


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Shared spike days :", shared_spike_days)
    print("Isolated spike days:", len(isolated_spike_days))
    print(summary)
    build_chart_rq4(5).show()
    build_chart_rq4_category_breakdown("gold_close", 5).show()