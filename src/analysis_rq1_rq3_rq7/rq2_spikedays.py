#How do MSCI World, Gold, and Bitcoin differ in the direction and magnitude of their cumulative 3-day price returns
# following identical Trump-related news events in the Guardian across all three news categories?

#Find Spike days, that match in all news types
#calculate the x day price return for each spike day and each asset class
#compare the price return using a grouped bar chart

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from glob import glob

#-- Global Filepaths ----------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_MARKET         = os.path.join(BASE_DIR, "../../data/processed/market_daily.csv")
DATA_NEWS_COUNTS    = os.path.join(BASE_DIR, "../../data/processed/article_counts.csv")

#-- Category columns in the article count file --------------------------------
CATEGORY_COLUMNS = {
    "trade":       "trade_policy_count",
    "geopolitics": "geopolitics_count",
    "domestic":    "domestic_politics_count",
}

# ── Colour palette (consistent across all charts) ────────────────────────────
ASSET_COLORS = {
    "gold_close":       "#F5C518",   # warm gold
    "bitcoin_close":    "#4A90D9",   # royal blue
    "msci_world_close": "#27AE60",   # green
}
ASSET_LABELS = {
    "gold_close":       "Gold",
    "bitcoin_close":    "Bitcoin",
    "msci_world_close": "MSCI World",
}

#-- Load article counts -----------------------------------------
counts_df = pd.read_csv(DATA_NEWS_COUNTS)
counts_df["date"] = pd.to_datetime(counts_df["date"])


def get_spike_days_of_single_class(df, column, sensitivity=1):
    """Get spike days for a single category column from the counts DataFrame."""
    average   = df[column].mean()
    std_dev   = df[column].std()
    threshold = average + sensitivity * std_dev

    spike_series = df[df[column] > threshold].set_index("date")[column]
    spike_series.index = pd.to_datetime(spike_series.index)
    return spike_series


def get_shared_spike_days(spike_days_list):
    """Return deduplicated dates that spike in ALL provided categories."""

    def remove_duplicate_spike_days(spike_days):
        MIN_GAP_DAYS = 5
        filtered_spike_days = []
        last_kept_date = None

        for date in spike_days:
            if last_kept_date is None:
                filtered_spike_days.append(date)
                last_kept_date = date
            else:
                gap = (pd.to_datetime(date) - pd.to_datetime(last_kept_date)).days
                if gap >= MIN_GAP_DAYS:
                    filtered_spike_days.append(date)
                    last_kept_date = date

        return filtered_spike_days

    sets   = [set(lst.index) for lst in spike_days_list]
    shared = sorted(sets[0].intersection(*sets[1:])) if sets else []

    return remove_duplicate_spike_days(shared)


def load_price_data(filepath):
    """Load the market_daily.csv which has columns: date, gold, bitcoin, msci_world"""
    df = pd.read_csv(filepath, index_col=0, parse_dates=True)
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    return df


def calculate_price_return(spike_days, daily_close, days_after=3, pre_event_days=5):
    """Calculate abnormal returns for a list of spike days against a price Series."""

    def get_nearest_price(series, date):
        for offset in range(4):
            try:
                return series.loc[date + pd.Timedelta(days=offset)]
            except KeyError:
                continue
        return None

    results = []

    for spike_day in spike_days:
        date = pd.to_datetime(spike_day)

        price_anchor = get_nearest_price(daily_close, date - pd.Timedelta(days=1))
        price_day0   = get_nearest_price(daily_close, date)
        price_end    = get_nearest_price(daily_close, date + pd.Timedelta(days=days_after))

        if any(p is None for p in [price_anchor, price_day0, price_end]):
            continue

        # Pre-event trend
        pre_event_returns = []
        for d in range(1, pre_event_days + 1):
            p_start = get_nearest_price(daily_close, date - pd.Timedelta(days=d + 1))
            p_end   = get_nearest_price(daily_close, date - pd.Timedelta(days=d))
            if p_start is not None and p_end is not None:
                pre_event_returns.append((p_end - p_start) / p_start * 100)

        expected_daily_return = sum(pre_event_returns) / len(pre_event_returns) if pre_event_returns else 0
        expected_total        = expected_daily_return * (days_after + 1)

        raw_return_day0 = (price_day0 - price_anchor) / price_anchor * 100
        raw_return_end  = (price_end  - price_anchor) / price_day0  * 100
        abnormal_return = raw_return_end - expected_total

        normal_std = daily_close.pct_change().std() * 100
        z_score    = abnormal_return / normal_std if normal_std > 0 else 0

        results.append({
            "date":               date.strftime("%Y-%m-%d"),
            "return_day0_%":      round(raw_return_day0, 2),
            "raw_return_%":       round(raw_return_end, 2),
            "expected_drift_%":   round(expected_total, 2),
            "abnormal_return_%":  round(abnormal_return, 2),
            "z_score":            round(z_score, 2),
            "significant":        abs(z_score) > 1.3
        })

    return pd.DataFrame(results)

def _get_nearest_price(series, date):
    """Module-level utility: find the closest available price within ±3 trading days."""
    for offset in range(4):
        try:
            return series.loc[date + pd.Timedelta(days=offset)]
        except KeyError:
            continue
    return None
#-- Build spike days from the new counts file ------------

single_category_spike_days = [
    (label, get_spike_days_of_single_class(counts_df, col))
    for label, col in CATEGORY_COLUMNS.items()
]

shared_spike_days = get_shared_spike_days([s for _, s in single_category_spike_days])

#-- Load market data ----------------------------
market_df = load_price_data(DATA_MARKET)

# Build per-asset Series dict  {asset_name: pd.Series}
ASSET_COLUMNS = ["gold_close", "bitcoin_close", "msci_world_close"]
all_daily_closes = {col: market_df[col].dropna() for col in ASSET_COLUMNS if col in market_df.columns}
all_daily_returns = all_daily_closes

# ── Build results DataFrame ───────────────────────────────────────────────────
all_results = []

for asset, daily_close in all_daily_closes.items():
    price_returns = calculate_price_return(shared_spike_days, daily_close, days_after=3)
    price_returns["asset"] = asset
    all_results.append(price_returns)

df_all = pd.concat(all_results, ignore_index=True)


# ── Website chart functions ───────────────────────────────────────────────────

#Chart 1 Dot/ Strip Plot
#each dot = one event
#open circle = not significant, closed = significant

def build_chart1(days_after):
    fig = go.Figure()
 
    for asset, daily_close in all_daily_closes.items():
        df  = calculate_price_return(shared_spike_days, daily_close, days_after=days_after)
        if df.empty:
            continue
 
        sig     = df[df["significant"] == True]
        not_sig = df[df["significant"] == False]
        color   = ASSET_COLORS.get(asset, "#888")
        label   = ASSET_LABELS.get(asset, asset)
 
        # Significant events — filled circle, black border
        if not sig.empty:
            fig.add_trace(go.Scatter(
                name=f"{label} ★",
                x=sig["date"],
                y=sig["abnormal_return_%"],
                mode="markers",
                marker=dict(
                    color=color, size=13,
                    symbol="circle",
                    line=dict(color="black", width=1.5),
                ),
                customdata=sig[["z_score", "expected_drift_%"]].values,
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    f"<b>{label}</b><br>"
                    "Abnormal Return: <b>%{y:.2f}%</b><br>"
                    "Z-Score: %{customdata[0]:.2f}  ★ significant<br>"
                    "Expected drift: %{customdata[1]:.2f}%"
                    "<extra></extra>"
                ),
            ))
 
        # Non-significant events — open circle
        if not not_sig.empty:
            fig.add_trace(go.Scatter(
                name=label,
                x=not_sig["date"],
                y=not_sig["abnormal_return_%"],
                mode="markers",
                marker=dict(
                    color="rgba(0,0,0,0)", size=11,
                    symbol="circle",
                    line=dict(color=color, width=2),
                ),
                customdata=not_sig[["z_score", "expected_drift_%"]].values,
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    f"<b>{label}</b><br>"
                    "Abnormal Return: <b>%{y:.2f}%</b><br>"
                    "Z-Score: %{customdata[0]:.2f}<br>"
                    "Expected drift: %{customdata[1]:.2f}%"
                    "<extra></extra>"
                ),
            ))
 
    fig.add_hline(y=0, line_dash="dash", line_color="black", line_width=1)
 
    fig.update_layout(
        title=f"Abnormal Returns per Event — {days_after} Days After Spike<br>"
              f"<sup>Solid = statistically significant (|z| > 1.3) &nbsp;·&nbsp; Open = not significant</sup>",
        xaxis_title="Event Date",
        yaxis_title="Abnormal Return (%)",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=500,
        hovermode="x unified",
        legend=dict(orientation="h", y=-0.18),
        xaxis=dict(showgrid=True, gridcolor="#eee"),
        yaxis=dict(showgrid=True, gridcolor="#eee", zeroline=False),
    )
    return fig


#chart 2
#candlestick Chart
#one subplot per asset


def build_chart2(event, days_before, days_after):
    assets      = list(all_daily_closes.keys())
    n_assets    = len(assets)
    date        = pd.to_datetime(event)
    x_labels    = list(range(-days_before, days_after + 1))
 
    fig = make_subplots(
        rows=n_assets, cols=1,
        shared_xaxes=True,
        subplot_titles=[ASSET_LABELS.get(a, a) for a in assets],
        vertical_spacing=0.08,
    )
 
    for row, asset in enumerate(assets, start=1):
        daily_close = all_daily_closes[asset]
 
        # Collect raw prices for the window
        raw_prices = []
        for offset in x_labels:
            p = _get_nearest_price(daily_close, date + pd.Timedelta(days=offset))
            raw_prices.append(p if p is not None else float("nan"))
 
        # Normalise to 100 at day −1 (index = days_before − 1)
        anchor_idx = days_before - 1
        anchor     = raw_prices[anchor_idx] if raw_prices[anchor_idx] else 1.0
        norm       = [(p / anchor * 100) if not pd.isna(p) else float("nan") for p in raw_prices]
 
        # Build synthetic OHLC
        opens, closes, highs, lows = [], [], [], []
        for i, c in enumerate(norm):
            o = norm[i - 1] if i > 0 and not pd.isna(norm[i - 1]) else c
            opens.append(o)
            closes.append(c)
            highs.append(max(o, c) * 1.002 if not pd.isna(c) else float("nan"))
            lows.append(min(o, c) * 0.998  if not pd.isna(c) else float("nan"))
 
        color = ASSET_COLORS.get(asset, "#888")
 
        fig.add_trace(
            go.Candlestick(
                name=ASSET_LABELS.get(asset, asset),
                x=x_labels,
                open=opens, high=highs, low=lows, close=closes,
                increasing=dict(line=dict(color=color), fillcolor=color),
                decreasing=dict(line=dict(color="#e74c3c"), fillcolor="#e74c3c"),
                hovertext=[
                    f"Day {d:+d}  |  Norm. close: {c:.2f}"
                    for d, c in zip(x_labels, closes)
                ],
                showlegend=False,
            ),
            row=row, col=1,
        )
 
        # Baseline at 100
        fig.add_hline(
            y=100, line_dash="dot", line_color="gray",
            line_width=1, row=row, col=1,
        )
 
        # Y-axis label per subplot
        fig.update_yaxes(
            title_text="Norm. price",
            showgrid=True, gridcolor="#eee",
            row=row, col=1,
        )
 
    # Vertical line at day 0
    for row in range(1, n_assets + 1):
        fig.add_vline(x=0, line_dash="dash", line_color="red")

    fig.add_annotation(
        x=0, y=1.02, xref="x", yref="paper",
        text="📰 News spike", showarrow=False,
        font=dict(color="red", size=11),
    )
 
    fig.update_layout(
        title=f"Price Action Around Spike Event: {event}<br>"
              f"<sup>Normalised to 100 at day −1 &nbsp;·&nbsp; "
              f"Green candle = price ↑ from prev day &nbsp;·&nbsp; Red = price ↓</sup>",
        xaxis_title="Days relative to news spike",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=220 * n_assets + 80,
        xaxis=dict(showgrid=True, gridcolor="#eee"),
    )

    fig.update_xaxes(rangeslider_visible=False)
    return fig


#chart 3
#comulatice abnormal return - waterfall chart


def build_chart3(event, days_after):
    """Waterfall: cumulative abnormal return building day-by-day after the event."""
    assets   = list(all_daily_closes.keys())
    n_assets = len(assets)
    date     = pd.to_datetime(event)
 
    fig = make_subplots(
        rows=1, cols=n_assets,
        subplot_titles=[ASSET_LABELS.get(a, a) for a in assets],
        shared_yaxes=False,
        horizontal_spacing=0.10,
    )
 
    for col_idx, asset in enumerate(assets, start=1):
        daily_close  = all_daily_closes[asset]
        normal_std   = daily_close.pct_change().std() * 100
 
        # Pre-event expected daily return (5-day lookback)
        pre_returns = []
        for d in range(1, 6):
            p_s = _get_nearest_price(daily_close, date - pd.Timedelta(days=d + 1))
            p_e = _get_nearest_price(daily_close, date - pd.Timedelta(days=d))
            if p_s and p_e:
                pre_returns.append((p_e - p_s) / p_s * 100)
        expected_daily = sum(pre_returns) / len(pre_returns) if pre_returns else 0
 
        # Daily incremental abnormal returns: day 0 … day N
        day_labels, increments, measures = [], [], []
        p_prev = _get_nearest_price(daily_close, date - pd.Timedelta(days=1))
 
        for d in range(0, days_after + 1):
            p_curr = _get_nearest_price(daily_close, date + pd.Timedelta(days=d))
            if p_prev is None or p_curr is None:
                continue
            raw_daily    = (p_curr - p_prev) / p_prev * 100
            abnormal_day = raw_daily - expected_daily
            day_labels.append(f"Day {d}")
            increments.append(round(abnormal_day, 3))
            measures.append("relative")
            p_prev = p_curr
 
        # Final total bar
        day_labels.append("Total")
        increments.append(round(sum(increments), 3))
        measures.append("total")
 
        color  = ASSET_COLORS.get(asset, "#888")
 
        # Waterfall colours: positive = asset colour, negative = red, total = dark grey
        increasing_color = color
        decreasing_color = "#e74c3c"
        totals_color     = "#2c3e50"
 
        fig.add_trace(
            go.Waterfall(
                name=ASSET_LABELS.get(asset, asset),
                orientation="v",
                measure=measures,
                x=day_labels,
                y=increments,
                connector=dict(line=dict(color="#ccc", width=1, dash="dot")),
                increasing=dict(marker=dict(color=increasing_color)),
                decreasing=dict(marker=dict(color=decreasing_color)),
                totals=dict(marker=dict(color=totals_color)),
                text=[f"{v:+.2f}%" for v in increments],
                textposition="outside",
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Daily abnormal return: %{y:+.2f}%"
                    "<extra></extra>"
                ),
                showlegend=False,
            ),
            row=1, col=col_idx,
        )
 
        fig.add_hline(
            y=0, line_dash="dash", line_color="black",
            line_width=1, row=1, col=col_idx,
        )
        fig.update_yaxes(
            title_text="Abnormal return (%)" if col_idx == 1 else "",
            showgrid=True, gridcolor="#eee",
            row=1, col=col_idx,
        )
 
    fig.update_layout(
        title=f"Cumulative Abnormal Return After Spike Event: {event}<br>"
              f"<sup>Each bar = daily incremental abnormal return &nbsp;·&nbsp; "
              f"'Total' bar = cumulative sum &nbsp;·&nbsp; "
              f"Green = above expected &nbsp;·&nbsp; Red = below expected</sup>",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=480,
    )
    return fig