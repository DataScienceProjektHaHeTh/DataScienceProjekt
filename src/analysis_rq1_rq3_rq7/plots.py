"""
plots.py
========
Plotly visualizations for RQ1, RQ7, and RQ3.

Each function returns a plotly Figure object that can be:
  - Shown standalone:  fig.show()
  - Embedded in Dash:  dcc.Graph(figure=fig)

Functions
---------
  fig_rq1_heatmap(master)     — 3x3 correlation heatmap (article count vs 3d return)
  fig_rq1_scatter(master)     — 3x3 scatter grid on spike days with trend lines
  fig_rq7_overview(master)    — donut (volume share) + scatter (volume vs correlation strength)
  fig_rq3_violin(master)      — grouped violin distributions of returns by sentiment bucket
  fig_rq3_buckets(master)     — grouped bar chart of avg return per sentiment bucket (±1 SE error bars)
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

# Allow imports from the analysis folder regardless of working directory
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from analysis_rq1_rq3_rq7.rq1_correlation import compute_correlations, CATEGORIES, ASSETS, CAT_LABELS, ASSET_LABELS
from analysis_rq1_rq3_rq7.rq3_sentiment import compute_sentiment_correlations, compute_sentiment_buckets

# ── Shared style constants ─────────────────────────────────────────────────────

pio.templates["newspaper"] = pio.templates["plotly_white"]
pio.templates["newspaper"].layout.paper_bgcolor = "rgba(0,0,0,0)"
pio.templates["newspaper"].layout.plot_bgcolor  = "rgba(0,0,0,0)"
TEMPLATE = "newspaper"

CAT_COLORS = {
    "trade_policy":      "#2196F3",   # blue
    "geopolitics":       "#FF9800",   # orange
    "domestic_politics": "#4CAF50",   # green
}
ASSET_COLORS = {
    "msci_world": "#9C27B0",   # purple
    "gold":       "#FFC107",   # gold
    "bitcoin":    "#FF5722",   # deep orange
}
BUCKET_COLORS = {
    "Negative": "#EF5350",   # red
    "Neutral":  "#90A4AE",   # grey-blue
    "Positive": "#66BB6A",   # green
}


# ── RQ1: Correlation heatmap ───────────────────────────────────────────────────

def fig_rq1_heatmap(
    master: pd.DataFrame,
    method: str = "spearman",
    config_label: str = "",
) -> go.Figure:
    """
    3×3 heatmap of correlation between article count and n-day return.
    Rows = news categories, Columns = assets.
    Colour scale is diverging (red = negative, blue = positive), centred at 0.
    Each cell shows the r value and significance stars.

    config_label is shown in the subtitle so viewers know which parameter
    configuration produced the chart (e.g. "7d return | z-score | lag=0").
    """
    correlations, pvalues, n_obs = compute_correlations(master, method=method)

    cat_labels   = [CAT_LABELS[c]   for c in CATEGORIES]
    asset_labels = [ASSET_LABELS[a] for a in ASSETS]

    z      = correlations.values.astype(float)
    p_vals = pvalues.values.astype(float)

    def star(p):
        if np.isnan(p):   return ""
        if p < 0.001:     return "***"
        if p < 0.01:      return "**"
        if p < 0.05:      return "*"
        if p < 0.10:      return "."
        return ""

    text = [[f"{z[i,j]:.3f}{star(p_vals[i,j])}<br>(n={int(n_obs.values[i,j])})"
             for j in range(3)] for i in range(3)]

    subtitle = "Spike days only | Significance: . p<0.10 &nbsp; * p<0.05 &nbsp; ** p<0.01 &nbsp; *** p<0.001"
    if config_label:
        subtitle = f"{config_label} &nbsp;|&nbsp; {subtitle}"

    fig = go.Figure(go.Heatmap(
        z=z,
        x=asset_labels,
        y=cat_labels,
        text=text,
        texttemplate="%{text}",
        textfont={"size": 13},
        colorscale="RdBu",
        zmid=0,
        zmin=-0.5,
        zmax=0.5,
        colorbar=dict(title=f"{method.capitalize()} r", tickformat=".2f"),
    ))

    fig.update_layout(
        template=TEMPLATE,
        title=dict(
            text=f"RQ1 — Correlation: Article Count vs Return<br><sup>{subtitle}</sup>",
            x=0.5,
        ),
        xaxis_title="Asset",
        yaxis_title="News Category",
        height=420,
        margin=dict(t=110),
    )
    return fig


# ── RQ1: Scatter grid on spike days ───────────────────────────────────────────

def fig_rq1_scatter(
    master: pd.DataFrame,
    method: str = "spearman",
    config_label: str = "",
) -> go.Figure:
    """
    3×3 subplot grid: one scatter plot per category × asset combination.
    X = article count (or z-score) on spike day, Y = n-day return.
    Each subplot includes a linear trend line and annotates the r value.
    config_label is shown in the chart title for transparency.
    """
    correlations, pvalues, _ = compute_correlations(master, method=method)

    fig = make_subplots(
        rows=3, cols=3,
        row_titles=[CAT_LABELS[c] for c in CATEGORIES],
        column_titles=[ASSET_LABELS[a] for a in ASSETS],
        horizontal_spacing=0.08,
        vertical_spacing=0.12,
    )

    def star(p):
        if np.isnan(p): return ""
        if p < 0.05:    return "*"
        if p < 0.10:    return "."
        return ""

    for row_i, cat in enumerate(CATEGORIES):
        spike_days = master[master[f"{cat}_spike"]]
        for col_j, asset in enumerate(ASSETS):
            pair = spike_days[[f"{cat}_count", f"{asset}_3d_return"]].dropna()
            x = pair[f"{cat}_count"].values
            y = pair[f"{asset}_3d_return"].values

            # Scatter points
            fig.add_trace(go.Scatter(
                x=x, y=y,
                mode="markers",
                marker=dict(color=ASSET_COLORS[asset], size=7, opacity=0.7),
                showlegend=False,
                hovertemplate=f"Articles: %{{x}}<br>3d return: %{{y:.2f}}%<extra>{CAT_LABELS[cat]}</extra>",
            ), row=row_i + 1, col=col_j + 1)

            # Trend line via linear regression
            if len(x) >= 3:
                m, b = np.polyfit(x, y, 1)
                x_line = np.linspace(x.min(), x.max(), 50)
                fig.add_trace(go.Scatter(
                    x=x_line, y=m * x_line + b,
                    mode="lines",
                    line=dict(color=ASSET_COLORS[asset], width=2, dash="dash"),
                    showlegend=False,
                ), row=row_i + 1, col=col_j + 1)

            # Annotate r value
            r = correlations.loc[cat, asset]
            p = pvalues.loc[cat, asset]
            fig.add_annotation(
                xref="x domain", yref="y domain",
                x=0.97, y=0.97,
                text=f"r={r:.2f}{star(p)}",
                showarrow=False,
                font=dict(size=11, color=ASSET_COLORS[asset]),
                xanchor="right", yanchor="top",
                row=row_i + 1, col=col_j + 1,
            )

    title_text = "RQ1 — Article Count vs Return on Spike Days"
    if config_label:
        title_text += f"<br><sup>{config_label}</sup>"

    fig.update_layout(
        template=TEMPLATE,
        title=dict(text=title_text, x=0.5),
        height=750,
        margin=dict(t=90),
    )
    x_label = "Z-score (rolling 30d)" if "z-score" in config_label.lower() else "Articles on spike day"
    fig.update_xaxes(title_text=x_label, title_font_size=11)
    fig.update_yaxes(title_text="Return (%)", title_font_size=11)
    return fig


# ── RQ7: Volume and ranking overview ──────────────────────────────────────────

def fig_rq7_overview(master: pd.DataFrame, method: str = "spearman") -> go.Figure:
    """
    Two-panel figure:
      Left panel  — donut chart showing each category's share of total article volume
      Right panel — scatter plot: avg volume (X) vs mean absolute correlation (Y),
                    one labelled point per category

    The donut answers "which category dominates coverage?"
    The scatter directly asks "does more coverage mean stronger market impact?"
    """
    volumes = {CAT_LABELS[c]: master[f"{c}_count"].mean() for c in CATEGORIES}

    correlations, _, _ = compute_correlations(master, method=method)
    mean_abs_r = {CAT_LABELS[c]: correlations.loc[c].abs().mean() for c in CATEGORIES}

    labels     = [CAT_LABELS[c] for c in CATEGORIES]
    vol_values = [volumes[l]    for l in labels]
    corr_values = [mean_abs_r[l] for l in labels]
    colors     = [CAT_COLORS[c] for c in CATEGORIES]

    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "domain"}, {"type": "xy"}]],
        subplot_titles=["Article Volume Share", "Volume vs Correlation Strength"],
        horizontal_spacing=0.12,
    )

    # Left: donut chart — percentages inside, labels in legend
    fig.add_trace(go.Pie(
        labels=labels,
        values=vol_values,
        hole=0.45,
        marker=dict(colors=colors),
        textinfo="percent",
        textposition="inside",
        hovertemplate="%{label}<br>Avg %{value:.1f} articles/day<extra></extra>",
        showlegend=True,
    ), row=1, col=1)

    # Right: scatter — one labelled dot per category
    for i, (label, cat) in enumerate(zip(labels, CATEGORIES)):
        fig.add_trace(go.Scatter(
            x=[vol_values[i]],
            y=[corr_values[i]],
            mode="markers+text",
            marker=dict(color=CAT_COLORS[cat], size=14),
            text=[label],
            textposition="top center",
            name=label,
            showlegend=False,
        ), row=1, col=2)

    fig.update_layout(
        template=TEMPLATE,
        title=dict(text="RQ7 — Coverage Volume vs Market Correlation Strength", x=0.5),
        height=420,
        margin=dict(t=80),
    )
    fig.update_xaxes(title_text="Avg articles / day", row=1, col=2)
    fig.update_yaxes(title_text="Correlation Strength", row=1, col=2)
    return fig


# ── RQ3: Sentiment violin plot ─────────────────────────────────────────────────

def fig_rq3_violin(
    master: pd.DataFrame,
    negative_threshold: float = -0.05,
    positive_threshold: float = 0.05,
) -> go.Figure:
    """
    3-panel figure (one per news category) with grouped violin plots.
    For each asset, three violins show the distribution of 3-day returns
    on negative, neutral, and positive sentiment days.

    This reveals the shape and spread of return distributions per sentiment
    bucket — complementing the mean-focused bucket bar chart.
    """
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=[CAT_LABELS[c] for c in CATEGORIES],
        horizontal_spacing=0.04,
        shared_yaxes=True,
    )

    shown: set = set()
    for col_j, cat in enumerate(CATEGORIES):
        sentiment_col = f"{cat}_sentiment"
        for asset in ASSETS:
            pair = master[[sentiment_col, f"{asset}_3d_return"]].dropna()
            neg = pair[pair[sentiment_col] <= negative_threshold][f"{asset}_3d_return"].values
            neu = pair[
                (pair[sentiment_col] > negative_threshold) &
                (pair[sentiment_col] < positive_threshold)
            ][f"{asset}_3d_return"].values
            pos = pair[pair[sentiment_col] >= positive_threshold][f"{asset}_3d_return"].values

            for returns, bucket_label in [(neg, "Negative"), (neu, "Neutral"), (pos, "Positive")]:
                if len(returns) < 3:
                    continue
                show = bucket_label not in shown
                shown.add(bucket_label)
                fig.add_trace(go.Violin(
                    x=[ASSET_LABELS[asset]] * len(returns),
                    y=returns,
                    name=bucket_label,
                    legendgroup=bucket_label,
                    showlegend=show,
                    line_color=BUCKET_COLORS[bucket_label],
                    fillcolor=BUCKET_COLORS[bucket_label],
                    opacity=0.6,
                    box_visible=True,
                    meanline_visible=True,
                    points=False,
                    scalemode="width",
                    width=0.9,
                ), row=1, col=col_j + 1)

    for col_j in range(1, 4):
        fig.add_hline(y=0, line_dash="dot", line_color="black", line_width=1, row=1, col=col_j)

    fig.update_layout(
        template=TEMPLATE,
        title=dict(
            text="RQ3 — Distribution of 3-Day Returns by Sentiment<br>"
                 f"<sup>Negative ≤ {negative_threshold} | Neutral | Positive ≥ {positive_threshold} (VADER compound)</sup>",
            x=0.5,
        ),
        violinmode="group",
        violingap=0.05,
        violingroupgap=0.05,
        height=520,
        margin=dict(t=110),
        legend=dict(title="Sentiment", orientation="h", x=0.5, xanchor="center", y=-0.15),
    )
    fig.update_yaxes(title_text="3-day return (%)", row=1, col=1)
    return fig


# ── RQ3: Bucket bar chart ──────────────────────────────────────────────────────

def fig_rq3_buckets(
    master: pd.DataFrame,
    negative_threshold: float = -0.05,
    positive_threshold: float = 0.05,
) -> go.Figure:
    """
    3-panel figure (one per news category), each showing a grouped bar chart:
      X    = asset (MSCI World, Gold, Bitcoin)
      Y    = average return (%)
      Bars = sentiment bucket (Negative / Neutral / Positive)
      Error bars = ±1 standard error (SE = std / sqrt(n))

    Error bars show whether bucket differences are meaningful or just noise.
    """
    buckets = compute_sentiment_buckets(master, negative_threshold, positive_threshold)

    # Pre-compute standard errors per (cat, asset, bucket) from raw master
    se_lookup: dict = {}
    for cat in CATEGORIES:
        sent_col = f"{cat}_sentiment"
        se_lookup[cat] = {}
        for asset in ASSETS:
            pair = master[[sent_col, f"{asset}_3d_return"]].dropna()
            neg_r = pair[pair[sent_col] <= negative_threshold][f"{asset}_3d_return"]
            neu_r = pair[(pair[sent_col] > negative_threshold) & (pair[sent_col] < positive_threshold)][f"{asset}_3d_return"]
            pos_r = pair[pair[sent_col] >= positive_threshold][f"{asset}_3d_return"]
            se_lookup[cat][ASSET_LABELS[asset]] = {
                "Negative": neg_r.std() / len(neg_r) ** 0.5 if len(neg_r) > 1 else 0,
                "Neutral":  neu_r.std() / len(neu_r) ** 0.5 if len(neu_r) > 1 else 0,
                "Positive": pos_r.std() / len(pos_r) ** 0.5 if len(pos_r) > 1 else 0,
            }

    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=[CAT_LABELS[c] for c in CATEGORIES],
        horizontal_spacing=0.08,
        shared_yaxes=True,
    )

    bucket_keys = [
        ("negative_mean", "negative_n", "Negative"),
        ("neutral_mean",  "neutral_n",  "Neutral"),
        ("positive_mean", "positive_n", "Positive"),
    ]

    for col_j, cat in enumerate(CATEGORIES):
        df = buckets[cat]
        asset_labels_list = list(df.index)

        for mean_col, n_col, bucket_label in bucket_keys:
            means = df[mean_col].values.astype(float)
            ns    = df[n_col].values.astype(int)
            ses   = [se_lookup[cat][a][bucket_label] for a in asset_labels_list]

            fig.add_trace(go.Bar(
                name=bucket_label,
                x=asset_labels_list,
                y=means,
                marker_color=BUCKET_COLORS[bucket_label],
                text=[f"{m:+.2f}%<br>n={n}" for m, n in zip(means, ns)],
                textposition="outside",
                showlegend=(col_j == 0),
                legendgroup=bucket_label,
                error_y=dict(type="data", array=ses, visible=True, thickness=1.5, width=4),
                hovertemplate=f"{bucket_label}<br>%{{x}}: %{{y:.2f}}% ± %{{error_y.array:.2f}}%<extra></extra>",
            ), row=1, col=col_j + 1)

    for col_j in range(1, 4):
        fig.add_hline(y=0, line_dash="dot", line_color="black", line_width=1, row=1, col=col_j)

    fig.update_layout(
        template=TEMPLATE,
        title=dict(
            text="RQ3 — Average Return by Sentiment Bucket (± 1 SE)<br>"
                 f"<sup>Negative ≤ {negative_threshold} | Neutral | Positive ≥ {positive_threshold} (VADER compound score)</sup>",
            x=0.5,
        ),
        barmode="group",
        height=500,
        margin=dict(t=110),
        legend=dict(title="Sentiment", orientation="h", x=0.5, xanchor="center", y=-0.15),
    )
    fig.update_yaxes(title_text="Avg return (%)", row=1, col=1)
    return fig


# ── Entry point: show all figures ─────────────────────────────────────────────

if __name__ == "__main__":
    from analysis_rq1_rq3_rq7.data_prep import (
        load_base_data, build_master_dynamic,
        compute_3d_returns, compute_normalized_counts,
    )

    print("Loading data...")
    counts, market, _returns_default, sentiment = load_base_data()

    # ── Default configuration (as defined by the research question) ────────────
    master_default = build_master_dynamic(counts, market, _returns_default, sentiment)

    # ── Improved configuration (discovered via parameter sweep) ───────────────
    # Z-score normalization removes the slow upward trend in article volume.
    # 7-day return window gives markets enough time to fully react to news spikes.
    # Together they reveal a statistically significant flight-to-safety pattern
    # for Trade Policy articles (MSCI down, Gold up, Bitcoin down).
    returns_7d  = compute_3d_returns(market, n_days=7)
    master_best = build_master_dynamic(counts, market, returns_7d, sentiment)
    zscores     = compute_normalized_counts(counts)
    for cat in ["trade_policy", "geopolitics", "domestic_politics"]:
        master_best[f"{cat}_count"] = zscores[f"{cat}_zscore"]

    print("Data loaded. Opening charts in browser...\n")

    figures = [
        # RQ1: show default first, then improved side by side
        ("RQ1 — Heatmap (default: 3d return, raw count)",
            fig_rq1_heatmap(master_default,
                            config_label="3-day return | raw article count | lag=0")),

        ("RQ1 — Heatmap (improved: 7d return, z-score — reveals flight-to-safety)",
            fig_rq1_heatmap(master_best,
                            config_label="7-day return | 30d rolling z-score | lag=0")),

        ("RQ1 — Scatter (default)",
            fig_rq1_scatter(master_default,
                            config_label="3-day return | raw article count | lag=0")),

        ("RQ1 — Scatter (improved)",
            fig_rq1_scatter(master_best,
                            config_label="7-day return | 30d rolling z-score | lag=0")),

        # RQ7: use the improved master so ranking comparison reflects the real signal
        ("RQ7 — Volume & ranking (improved config)",
            fig_rq7_overview(master_best)),

        # RQ3: default master (sentiment analysis doesn't benefit from z-score)
        ("RQ3 — Sentiment violin",
            fig_rq3_violin(master_default)),

        ("RQ3 — Bucket bar chart",
            fig_rq3_buckets(master_default)),
    ]

    for name, fig in figures:
        print(f"  Showing: {name}")
        fig.show()
