#Research question 4:
#To what degree does the co-occurrence of spikes across multiple news categories in the Guardian on the same day
# amplify the cumulative 3-day price return compared to days with an isolated single-category spike,
# and which asset class shows the greatest sensitivity to this multi-category overlap effect?

import pandas as pd
import os
import sys
import plotly.graph_objects as go
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rq2_spikedays import (
    get_spike_days_of_single_class,
    get_shared_spike_days,
    calculate_price_return,
    all_daily_closes,
    counts_df,
    CATEGORY_COLUMNS,
)

# RQ4 reuses all_daily_closes from RQ2 under the name all_daily_returns
all_daily_returns = all_daily_closes

# ── Rebuild per-category spike days from the counts file ─────────────────────
single_category_spike_days = [
    (label, get_spike_days_of_single_class(counts_df, col))
    for label, col in CATEGORY_COLUMNS.items()
]

shared_spike_days  = get_shared_spike_days([s for _, s in single_category_spike_days])


def get_isolated_spike_days(all_spike_days):
    """Find days that spike in EXACTLY ONE category."""
    all_dates = []
    for _, spike_days in all_spike_days:
        all_dates.extend(spike_days.index.tolist())

    date_counts = Counter(all_dates)
    isolated = sorted([date for date, count in date_counts.items() if count == 1])
    return isolated


isolated_spike_days = get_isolated_spike_days(single_category_spike_days)

# ── Build date → category set lookup ─────────────────────────────────────────
date_to_categories = {}
for label, spike_days in single_category_spike_days:
    for date in spike_days.index:
        date_to_categories.setdefault(date, set()).add(label)


# ── Module-level summary (printed when run directly) ─────────────────────────
DAYS_AFTER = 3
results = []

for asset_name, price_data in all_daily_returns.items():
    multi = calculate_price_return(shared_spike_days, price_data, DAYS_AFTER)
    multi["spike_type"] = "multi-category"
    multi["asset"] = asset_name

    single = calculate_price_return(isolated_spike_days, price_data, DAYS_AFTER)
    single["spike_type"] = "single-category"
    single["asset"] = asset_name

    results.extend([multi, single])

df_all = pd.concat(results, ignore_index=True)

summary = df_all.groupby(["asset", "spike_type"])["abnormal_return_%"].agg(
    avg_return="mean",
    median_return="median",
    std_return="std",
    count="count"
).reset_index()


# ── Website chart functions ───────────────────────────────────────────────────

def build_chart_rq4(days_after):
    """Grouped bar chart: avg abnormal return for single vs multi-category spikes."""
    colors = {"multi-category": "crimson", "single-category": "steelblue"}
    fig    = go.Figure()

    res = []
    for asset_name, price_data in all_daily_returns.items():
        multi = calculate_price_return(shared_spike_days, price_data, days_after)
        multi["spike_type"] = "multi-category"
        multi["asset"] = asset_name

        single = calculate_price_return(isolated_spike_days, price_data, days_after)
        single["spike_type"] = "single-category"
        single["asset"] = asset_name

        res.extend([multi, single])

    df = pd.concat(res, ignore_index=True)
    s  = df.groupby(["asset", "spike_type"])["abnormal_return_%"].mean().reset_index()
    s.columns = ["asset", "spike_type", "avg_return"]

    for spike_type in ["single-category", "multi-category"]:
        data = s[s["spike_type"] == spike_type]
        fig.add_trace(go.Bar(
            name=spike_type,
            x=data["asset"],
            y=data["avg_return"],
            marker_color=colors[spike_type],
            hovertemplate=(
                "<b>%{x}</b><br>" +
                f"Spike type: {spike_type}<br>" +
                "Avg abnormal return: %{y:.2f}%<extra></extra>"
            )
        ))

    fig.update_layout(
        title=f"RQ4: Single vs Multi-Category Spikes ({days_after}-day return)",
        xaxis_title="Asset",
        yaxis_title="Avg Abnormal Return (%)",
        barmode="group",
        plot_bgcolor="white",
        height=500,
        legend_title="Spike Type",
        shapes=[dict(
            type="line", x0=0, x1=1, xref="paper",
            y0=0, y1=0, yref="y",
            line=dict(color="black", width=1, dash="dash")
        )]
    )
    return fig


def build_chart_rq4_category_breakdown(asset_name, days_after):
    """Bar chart: avg return for one asset broken down by news category combination."""
    colors = {
        "all categories":    "crimson",
        "domestic only":     "steelblue",
        "trade only":        "goldenrod",
        "geopolitics only":  "seagreen",
        "domestic + trade":  "mediumpurple",
        "domestic + geopolitics": "darkorange",
        "trade + geopolitics":    "teal",
    }

    daily_close = all_daily_returns.get(asset_name)
    if daily_close is None:
        return go.Figure()

    # Group dates by their category combination
    combination_to_dates = {}
    for date, cats in date_to_categories.items():
        if len(cats) == len(single_category_spike_days):
            label = "all categories"
        elif len(cats) == 1:
            label = list(cats)[0] + " only"
        else:
            label = " + ".join(sorted(cats))
        combination_to_dates.setdefault(label, []).append(date)

    # Calculate avg return for each combination
    combo_results = []
    for label, dates in combination_to_dates.items():
        returns = calculate_price_return(dates, daily_close, days_after=days_after)
        if not returns.empty:
            combo_results.append({
                "combination": label,
                "avg_return":  round(returns["abnormal_return_%"].mean(), 2),
                "count":       len(returns)
            })

    if not combo_results:
        return go.Figure()

    df_combo = pd.DataFrame(combo_results).sort_values("avg_return", ascending=False)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_combo["combination"],
        y=df_combo["avg_return"],
        marker_color=[colors.get(c, "gray") for c in df_combo["combination"]],
        hovertemplate=(
            "<b>%{x}</b><br>" +
            "Avg abnormal return: %{y:.2f}%<br>" +
            "Events: %{customdata}<extra></extra>"
        ),
        customdata=df_combo["count"].values
    ))

    fig.update_layout(
        title=f"{asset_name}: Avg {days_after}-Day Return by News Category Combination",
        xaxis_title="News Category Combination",
        yaxis_title="Avg Abnormal Return (%)",
        plot_bgcolor="white",
        height=500,
        shapes=[dict(
            type="line", x0=0, x1=1, xref="paper",
            y0=0, y1=0, yref="y",
            line=dict(color="black", width=1, dash="dash")
        )]
    )
    return fig


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Shared spike days :", shared_spike_days)
    print("Isolated spike days:", len(isolated_spike_days))
    print(summary)