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
                marker=dict(size=6, color=color),
                hovertemplate=f"Day +%{{x}}<br>{label}: %{{y:.2f}}%<extra>{cat}</extra>",
            ), row=1, col=col_idx)

            # star at peak lag
            fig.add_trace(go.Scatter(
                x=[peak],
                y=[float(y_vals.loc[peak])],
                mode="markers",
                showlegend=False,
                marker=dict(symbol="star", size=13, color=color,
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
            font=dict(size=11, color="#888"),
            xanchor="right",
        )

        fig.update_xaxes(
            tickmode="array", tickvals=tick_vals, ticktext=tick_text,
            title_text="Days after spike", row=1, col=col_idx,
        )

    fig.update_yaxes(title_text="Avg cumulative return (%)", row=1, col=1)
    fig.update_layout(
        title="RQ6 — Avg cumulative return after spike by category",
        legend=dict(orientation="h", yanchor="top", y=-0.18, x=0.5, xanchor="center"),
        plot_bgcolor="#f8f9fa",
        paper_bgcolor="white",
        height=420,
        margin=dict(t=70, b=90, l=60, r=30),
    )
    return fig


def fig_rq6_peak_heatmap(
    df:               pd.DataFrame,
    spike_multiplier: float = 1.0,
    max_lag:          int   = 5,
) -> go.Figure:
    """
    Heatmap showing which lag day (1–max_lag) the cumulative return peaks for
    each (category × asset) combination.  Darker = later peak response.

    This gives a bird's-eye view: is Bitcoin always fastest? Does trade policy
    hit the market sooner than geopolitics?
    """
    results    = run_rq6(df=df, spike_multiplier=spike_multiplier, max_lag=max_lag)
    categories = list(results.keys())
    assets     = ["bitcoin", "gold", "msci_world"]

    z      = [[results[c]["peak_lags"][a] for a in assets] for c in categories]
    x_labs = [a.replace("_", " ").title() for a in assets]
    y_labs = [CATEGORY_LABELS.get(c, c) for c in categories]

    fig = go.Figure(go.Heatmap(
        z=z,
        x=x_labs,
        y=y_labs,
        text=[[f"Day +{v}" for v in row] for row in z],
        texttemplate="%{text}",
        colorscale="Blues",
        zmin=1, zmax=max_lag,
        colorbar=dict(title="Peak lag (day)", tickvals=list(range(1, max_lag + 1))),
        hovertemplate="Category: %{y}<br>Asset: %{x}<br>Peak at day +%{z}<extra></extra>",
    ))
    fig.update_layout(
        title="Peak response lag by category and asset (lower = faster reaction)",
        plot_bgcolor="#f8f9fa",
        paper_bgcolor="white",
        height=320,
        margin=dict(t=60, b=40, l=160, r=80),
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