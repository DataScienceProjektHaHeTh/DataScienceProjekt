import sys
from pathlib import Path

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Make "from data_loader import ..." work whether this module is run directly
# from src/analysis/ or imported as src.analysis.analysis_rq6 from the website.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from data_loader import build_master_df, add_spike_flags

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

# ── RQ6: lag analysis ─────────────────────────────────────────────────────────
# Core idea: for every spike day, look at the cumulative return on each of the
# following 5 days and find on which day the return peaks.
# Think of it like dropping a stone into water and timing how long until
# the wave reaches each shore (asset class).

def compute_cumulative_returns_from_spike(
    prices_df: pd.DataFrame,
    spike_date: pd.Timestamp,
    asset:      str,
    max_lag:    int = 5,
) -> pd.Series:
    """
    For a single spike date, computes the cumulative return at each lag day
    (day+1 through day+max_lag) relative to the closing price on spike day.

    Returns a Series indexed by lag (1, 2, 3, 4, 5) with % return values.
    """
    close_col = f"{asset}_close"

    try:
        base_price = prices_df.loc[spike_date, close_col]
    except KeyError:
        return pd.Series([np.nan] * max_lag, index=range(1, max_lag + 1))

    # get all available dates after the spike day
    future_dates = prices_df.index[prices_df.index > spike_date]

    returns_at_lag = {}
    for lag in range(1, max_lag + 1):
        if len(future_dates) >= lag:
            future_price = prices_df.iloc[
                prices_df.index.get_loc(spike_date) + lag
            ][close_col]
            returns_at_lag[lag] = (future_price - base_price) / base_price * 100
        else:
            returns_at_lag[lag] = np.nan

    return pd.Series(returns_at_lag)


def run_rq6(
    start_date:       str           = "2025-01-20",
    end_date:         str           = None,
    max_lag:          int           = 5,
    spike_multiplier: float         = 1.0,
    df:               pd.DataFrame  = None,   # pass pre-loaded df to skip raw-data reload
) -> dict:
    """
    RQ6: Within a 5-day window following a Trump-related Guardian coverage spike,
    how does the average price response lag to peak cumulative return differ
    across trade policy, geopolitics, and domestic politics?

    Parameters
    ----------
    start_date       : start of analysis window
    end_date         : end of analysis window
    max_lag          : maximum days after spike to look (default 5 = one trading week)
    spike_multiplier : std multiplier for spike detection (default 1.0)

    Returns
    -------
    dict with keys per category, each containing:
        - lag_profiles   : DataFrame of avg cumulative return at each lag per asset
        - peak_lags      : dict of {asset: avg lag day of peak return}
        - n_spikes       : number of spike days detected for this category
    """
    if df is None:
        df = build_master_df(start_date=start_date, end_date=end_date, return_window=max_lag)
    else:
        df = df.copy()
    df = add_spike_flags(df, spike_multiplier=spike_multiplier)

    categories  = ["trade_policy", "geopolitics", "domestic_politics"]
    assets      = ["bitcoin", "gold", "msci_world"]

    results = {}

    for cat in categories:
        spike_days = df[df[f"{cat}_spike"]].index
        n_spikes   = len(spike_days)

        # for each spike day and each asset, get the return profile over max_lag days
        # shape: (n_spikes × max_lag) per asset
        lag_data = {asset: [] for asset in assets}

        for spike_date in spike_days:
            for asset in assets:
                returns_series = compute_cumulative_returns_from_spike(
                    prices_df  = df,
                    spike_date = spike_date,
                    asset      = asset,
                    max_lag    = max_lag,
                )
                lag_data[asset].append(returns_series)

        # average the return profiles across all spike events per asset
        lag_profiles = pd.DataFrame({
            asset: pd.concat(
                [s.rename(i) for i, s in enumerate(lag_data[asset])],
                axis=1
            ).mean(axis=1)
            for asset in assets
        })
        lag_profiles.index.name = "lag_days"

        # find the lag day of peak absolute return for each asset
        peak_lags = {
            asset: int(lag_profiles[asset].abs().idxmax())
            for asset in assets
        }

        results[cat] = {
            "lag_profiles": lag_profiles,
            "peak_lags":    peak_lags,
            "n_spikes":     n_spikes,
        }

        print(f"\n── {cat.upper()} ({n_spikes} spike days) ──")
        print("   Average return profile (%) per lag day:")
        print(lag_profiles.round(3))
        print(f"   Peak lag per asset: {peak_lags}")

    return results


# ── plotly figures for web app ────────────────────────────────────────────────

def fig_rq6_lag_profiles(
    df:               pd.DataFrame,
    spike_multiplier: float = 1.0,
    max_lag:          int   = 5,
) -> go.Figure:
    """
    Three-panel figure (one subplot per news category) showing the average
    cumulative return (%) at each lag day 1–max_lag after a spike.
    Each subplot has one line per asset; a star marks the peak-return lag day.

    All categories are shown simultaneously so no dropdown is needed.

    Parameters
    ----------
    df               : pre-loaded master DataFrame (must include {asset}_close columns)
    spike_multiplier : std multiplier for spike detection
    max_lag          : maximum days to look forward (default 5)
    """
    results    = run_rq6(df=df, spike_multiplier=spike_multiplier, max_lag=max_lag)
    categories = ["trade_policy", "geopolitics", "domestic_politics"]
    assets     = ["bitcoin", "gold", "msci_world"]

    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=[CATEGORY_LABELS[c] for c in categories],
        shared_yaxes=True,
        horizontal_spacing=0.06,
    )

    tick_vals = list(range(1, max_lag + 1))
    tick_text = [f"+{i}" for i in tick_vals]

    for col_idx, cat in enumerate(categories, start=1):
        data         = results[cat]
        lag_profiles = data["lag_profiles"]
        peak_lags    = data["peak_lags"]
        n_spikes     = data["n_spikes"]

        for asset in assets:
            label  = asset.replace("_", " ").title()
            color  = ASSET_COLORS[asset]
            y_vals = lag_profiles[asset]
            peak   = peak_lags[asset]

            fig.add_trace(go.Scatter(
                x=tick_vals,
                y=y_vals.round(3),
                mode="lines+markers",
                name=label,
                legendgroup=label,
                showlegend=(col_idx == 1),   # only show in legend once
                line=dict(color=color, width=2),
                marker=dict(size=14, color=color),
                hovertemplate=f"Day +%{{x}}<br>{label}: %{{y:.2f}}%<extra>{cat}</extra>",
            ), row=1, col=col_idx)

            # star at peak lag
            fig.add_trace(go.Scatter(
                x=[peak],
                y=[float(y_vals.loc[peak])],
                mode="markers",
                showlegend=False,
                marker=dict(symbol="star", size=16, color=color,
                            line=dict(color="white", width=1)),
                hovertemplate=(
                    f"{label} peak: day +{peak} "
                    f"({float(y_vals.loc[peak]):.2f}%)<extra></extra>"
                ),
            ), row=1, col=col_idx)

        # zero reference line per subplot
        fig.add_hline(y=0, line_dash="dot", line_color="#aaa", line_width=1,
                      row=1, col=col_idx)

        # annotate spike count
        fig.add_annotation(
            text=f"n={n_spikes} spikes",
            xref=f"x{'' if col_idx == 1 else col_idx} domain",
            yref=f"y{'' if col_idx == 1 else col_idx} domain",
            x=0.98, y=0.02,
            showarrow=False,
            font=dict(size=16, color="#888"),
            xanchor="right",
        )

        fig.update_xaxes(
            tickmode="array", tickvals=tick_vals, ticktext=tick_text,
            title_text="Days after spike",
            title_font=dict(size=16), tickfont=dict(size=16),
            row=1, col=col_idx,
        )

    fig.update_yaxes(title_text="Avg cumulative return (%)",
                     title_font=dict(size=16), tickfont=dict(size=16), row=1, col=1)
    fig.update_layout(
        title=dict(
            text="RQ6 — Avg cumulative return after spike by category",
            font=dict(size=20),
        ),
        legend=dict(orientation="h", yanchor="top", y=-0.18, x=0.5, xanchor="center",
                    font=dict(size=16)),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=420,
        margin=dict(t=70, b=90, l=60, r=30),
        font = dict(size = 20)
    )
    fig.update_annotations(font_size=16)
    return fig


def fig_rq6_bubble(
    df:               pd.DataFrame,
    spike_multiplier: float = 1.0,
    max_lag:          int   = 5,
) -> go.Figure:
    """
    Bubble chart: for each (category × asset) pair, a bubble is placed at the
    peak lag day on the X axis, with the news category on the Y axis.

    Bubble size   = avg cumulative return magnitude at the peak lag day.
    Bubble colour = asset class.

    Bubbles within the same category row are offset slightly vertically so
    they do not overlap.  This communicates two things simultaneously:
      - WHERE the peak occurs (X position = lag day 1–5, i.e. how fast)
      - HOW LARGE the peak return is (bubble size, i.e. how strong)
    A plain heatmap can only show one of these at a time.
    """
    results    = run_rq6(df=df, spike_multiplier=spike_multiplier, max_lag=max_lag)
    categories = ["trade_policy", "geopolitics", "domestic_politics"]
    assets     = ["bitcoin", "gold", "msci_world"]

    # Vertical positions for each category row (integer) plus small per-asset offsets
    # so three bubbles in the same row don't sit on top of each other
    cat_y     = {cat: i for i, cat in enumerate(categories)}
    y_offsets = {"bitcoin": -0.22, "gold": 0.0, "msci_world": 0.22}

    # Bubble sizes are scaled from return magnitude; a minimum ensures tiny
    # returns still produce a visible marker
    SIZE_SCALE = 28
    MIN_SIZE   = 12

    fig = go.Figure()

    for asset in assets:
        label = asset.replace("_", " ").title()
        color = ASSET_COLORS[asset]

        x_vals, y_vals, sizes, hover_texts = [], [], [], []

        for cat in categories:
            data        = results[cat]
            peak_lag    = data["peak_lags"][asset]
            peak_return = float(data["lag_profiles"][asset].loc[peak_lag])

            x_vals.append(peak_lag)
            y_vals.append(cat_y[cat] + y_offsets[asset])
            sizes.append(max(abs(peak_return) * SIZE_SCALE, MIN_SIZE))
            hover_texts.append(
                f"<b>{label}</b> after {CATEGORY_LABELS[cat]} spike<br>"
                f"Peak lag: day +{peak_lag}<br>"
                f"Avg cumulative return: {peak_return:+.2f}%"
            )

        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="markers+text",
            name=label,
            marker=dict(
                size=sizes,
                color=color,
                opacity=0.80,
                line=dict(color="white", width=1.5),
                sizemode="diameter",
            ),
            text=[f"+{x}" for x in x_vals],   # lag day label inside bubble
            textposition="middle center",
            textfont=dict(size=14, color="white"),
            hovertext=hover_texts,
            hovertemplate="%{hovertext}<extra></extra>",
        ))

    fig.update_layout(
        title=dict(
            text=(
                "RQ6 — Peak response lag and magnitude by category and asset<br>"
                "<sup>X-position = day of peak cumulative return · "
                "bubble size = return magnitude at peak · colour = asset class</sup>"
            ),
            x=0.5,
            font=dict(size=20),
        ),
        xaxis=dict(
            title="Days after spike",
            title_font=dict(size=16),
            tickmode="array",
            tickvals=list(range(1, max_lag + 1)),
            ticktext=[f"Day +{i}" for i in range(1, max_lag + 1)],
            tickfont=dict(size=16),
            showgrid=True,
            gridcolor="#eee",
            range=[0.3, max_lag + 0.7],
        ),
        yaxis=dict(
            tickmode="array",
            tickvals=list(range(len(categories))),
            ticktext=[CATEGORY_LABELS[c] for c in categories],
            tickfont=dict(size=16),
            showgrid=True,
            gridcolor="#eee",
            range=[-0.6, len(categories) - 0.4],
        ),
        legend=dict(orientation="h", yanchor="top", y=-0.28, x=0.5, xanchor="center",
                    font=dict(size=16)),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=380,
        margin=dict(t=110, b=110, l=160, r=30),
    )
    return fig


# ── helper: peak lag summary for web app ─────────────────────────────────────
def get_peak_lag_summary(results: dict) -> pd.DataFrame:
    """
    Returns a clean summary table of peak response lags per category and asset
    for display in the web application.

    Shape: rows = categories, columns = assets
    """
    rows = []
    for cat, data in results.items():
        row = {"category": cat.replace("_", " ").title()}
        row.update({
            asset.replace("_", " ").title(): f"day +{lag}"
            for asset, lag in data["peak_lags"].items()
        })
        rows.append(row)
    return pd.DataFrame(rows).set_index("category")