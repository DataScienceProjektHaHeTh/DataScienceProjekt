#How do MSCI World, Gold, and Bitcoin differ in the direction and magnitude of their cumulative 3-day price returns
# following identical Trump-related news events in the Guardian across all three news categories?

#Find Spike days, that match in all news types
#calculate the x day price return for each spike day and each asset class
#compare the price return using a grouped bar chart

import pandas as pd
import plotly.graph_objects as go
import os
from glob import glob

#for global filepaths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_MARKET         = os.path.join(BASE_DIR, "../../data/processed/market_daily.csv")
DATA_NEWS_COUNTS    = os.path.join(BASE_DIR, "../../data/processed/article_counts.csv")

# ── Category columns in the article count file ───────────────────────────────
CATEGORY_COLUMNS = {
    "trade":       "trade_policy_count",
    "geopolitics": "geopolitics_count",
    "domestic":    "domestic_politics_count",
}

# ── Load article counts ───────────────────────────────────────────────────────
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


# ── Build spike days from the new counts file ─────────────────────────────────

single_category_spike_days = [
    (label, get_spike_days_of_single_class(counts_df, col))
    for label, col in CATEGORY_COLUMNS.items()
]

shared_spike_days = get_shared_spike_days([s for _, s in single_category_spike_days])

# ── Load market data ──────────────────────────────────────────────────────────
# market_daily.csv expected format:
#   date, gold, bitcoin, msci_world   (one row per day, already daily close prices)

market_df = load_price_data(DATA_MARKET)

# Build per-asset Series dict  {asset_name: pd.Series}
all_daily_closes = {col: market_df[col].dropna() for col in market_df.columns}

# ── Build results DataFrame ───────────────────────────────────────────────────
all_results = []

for asset, daily_close in all_daily_closes.items():
    price_returns = calculate_price_return(shared_spike_days, daily_close, days_after=3)
    price_returns["asset"] = asset
    all_results.append(price_returns)

df_all = pd.concat(all_results, ignore_index=True)


# ── Website chart functions ───────────────────────────────────────────────────

def build_chart1(days_after):
    """Grouped bar chart: abnormal returns per event, coloured by asset."""
    colors = {"gold_close": "gold", "bitcoin_close": "royalblue", "msci_world_close": "seagreen"}
    fig    = go.Figure()

    for asset, daily_close in all_daily_closes.items():
        df = calculate_price_return(shared_spike_days, daily_close, days_after=days_after)
        fig.add_trace(go.Bar(
            name=asset,
            x=df["date"],
            y=df["abnormal_return_%"],
            marker_color=colors.get(asset, "gray"),
            customdata=df[["z_score", "significant"]].values,
            hovertemplate=(
                "<b>%{x}</b><br>" +
                f"Asset: {asset}<br>" +
                "Abnormal Return: %{y:.2f}%<br>" +
                "Z-Score: %{customdata[0]}<br>" +
                "Significant: %{customdata[1]}<extra></extra>"
            )
        ))

    fig.update_layout(
        title=f"Abnormal Returns ({days_after} days after event)",
        barmode="group",
        hovermode="x unified",
        plot_bgcolor="white",
        height=500,
        shapes=[dict(
            type="line", x0=0, x1=1, xref="paper",
            y0=0, y1=0, yref="y",
            line=dict(color="black", width=1, dash="dash")
        )]
    )
    return fig


def build_chart2(event, days_before, days_after):
    """Normalised price path around a single event for all assets."""
    colors = {"gold_close": "gold_close", "bitcoin": "royalblue", "msci_world_close": "seagreen"}
    fig    = go.Figure()
    date   = pd.to_datetime(event)

    for asset, daily_close in all_daily_closes.items():
        path = []
        for offset in range(-days_before, days_after + 1):
            target = date + pd.Timedelta(days=offset)
            price  = None
            for adj in range(4):
                try:
                    price = daily_close.loc[target + pd.Timedelta(days=adj)]
                    break
                except KeyError:
                    continue
            path.append(price if price is not None else float("nan"))

        anchor    = path[days_before - 1] or 1
        path_norm = [(p / anchor) * 100 if p else float("nan") for p in path]

        fig.add_trace(go.Scatter(
            name=asset,
            x=list(range(-days_before, days_after + 1)),
            y=path_norm,
            mode="lines+markers",
            line=dict(color=colors.get(asset, "gray"), width=2),
        ))

    fig.update_layout(
        title=f"Price Path Around: {event}",
        xaxis_title="Days relative to news spike",
        yaxis_title="Normalized Price (day -1 = 100)",
        plot_bgcolor="white",
        height=500
    )
    fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="📰 News")
    fig.add_hline(y=100, line_dash="dot", line_color="gray")
    return fig


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Shared spike days:", shared_spike_days)
    print(df_all)