import json
import pandas as pd
from pathlib import Path

# ── paths ────────────────────────────────────────────────────────────────────
DATA_RAW = Path("data/raw")

GUARDIAN_FILES = {
    "trade_policy":      DATA_RAW / "guardian_trade_policy.json",
    "geopolitics":       DATA_RAW / "guardian_geopolitics.json",
    "domestic_politics": DATA_RAW / "guardian_domestic_politics.json",
}

MARKET_FILES = {
    "bitcoin":    DATA_RAW / "bitcoin_raw.csv",
    "gold":       DATA_RAW / "gold_raw.csv",
    "msci_world": DATA_RAW / "msci_world_raw.csv",
}

# ── guardian loader ───────────────────────────────────────────────────────────
def load_guardian_counts() -> pd.DataFrame:
    """
    Loads all three guardian category JSON files.
    Returns a DataFrame with one row per calendar day and one column
    per category containing the article count for that day.

    Shape: index=date, columns=[trade_policy, geopolitics, domestic_politics]
    """
    series_list = []

    for category, filepath in GUARDIAN_FILES.items():
        with open(filepath, "r") as f:
            articles = json.load(f)

        # extract publication date (date only, no time) for each article
        dates = [
            article["webPublicationDate"][:10]   # "2025-01-20T13:00:00Z" → "2025-01-20"
            for article in articles
        ]

        # count articles per day
        counts = (
            pd.Series(dates, name=category)
            .value_counts()
            .rename_axis("date")
            .sort_index()
        )
        series_list.append(counts)

    # combine all categories into one dataframe
    df = pd.concat(series_list, axis=1).fillna(0).astype(int)
    df.index = pd.to_datetime(df.index)
    return df


# ── market loader ─────────────────────────────────────────────────────────────
def load_market_prices() -> pd.DataFrame:
    """
    Loads all three market CSV files from yfinance.
    Handles yfinance's two-row header format automatically.
    Returns a DataFrame with one row per trading day and one column
    per asset containing the closing price.

    Shape: index=date, columns=[bitcoin, gold, msci_world]
    """
    series_list = []

    for asset, filepath in MARKET_FILES.items():
        # yfinance CSVs have a two-row header:
        # row 0: "Price", "Close", "High", ...
        # row 1: "Ticker", "BTC-USD", "BTC-USD", ...
        # we skip both and manually assign the date + close columns
        df_raw = pd.read_csv(filepath, header=[0, 1], index_col=0)

        # extract only the Close column
        close = df_raw["Close"].squeeze()  # squeeze drops the ticker sub-level
        close.name = asset
        close.index = pd.to_datetime(close.index)
        series_list.append(close)

    df = pd.concat(series_list, axis=1)
    df.index.name = "date"
    return df


# ── return calculator ─────────────────────────────────────────────────────────
def compute_returns(prices: pd.DataFrame, window: int = 3) -> pd.DataFrame:
    """
    Computes the cumulative n-day forward return for each asset.
    For each day t: return = (price[t+window] - price[t]) / price[t] * 100

    Parameters
    ----------
    prices : DataFrame of closing prices (output of load_market_prices)
    window : number of trading days to look forward (default 3 for RQ1-RQ4, 5 for RQ6)

    Returns
    -------
    DataFrame with same shape as prices, values are percentage returns
    """
    returns = prices.pct_change(periods=window).shift(-window) * 100
    returns.columns = [f"{col}_return_{window}d" for col in returns.columns]
    return returns


# ── master dataset builder ────────────────────────────────────────────────────
def build_master_df(
    start_date: str = "2025-01-20",
    end_date:   str = None,
    return_window: int = 3,
) -> pd.DataFrame:
    """
    Builds the single shared dataframe used by all analyses.
    Aligns guardian article counts with market returns on a daily index.

    Parameters
    ----------
    start_date    : first date to include (Trump's inauguration = "2025-01-20")
    end_date      : last date to include (None = today)
    return_window : forward return window in trading days

    Returns
    -------
    DataFrame with columns:
        - trade_policy, geopolitics, domestic_politics  (article counts)
        - bitcoin_return_Xd, gold_return_Xd, msci_world_return_Xd  (% returns)
        - bitcoin_close, gold_close, msci_world_close  (raw closing prices)
    """
    # load raw data
    guardian = load_guardian_counts()
    prices   = load_market_prices()
    returns  = compute_returns(prices, window=return_window)

    # rename price columns for clarity
    prices.columns = [f"{col}_close" for col in prices.columns]

    # combine everything on a shared daily index
    df = pd.concat([guardian, prices, returns], axis=1)

    # apply date filter
    df = df[df.index >= pd.Timestamp(start_date)]
    if end_date:
        df = df[df.index <= pd.Timestamp(end_date)]

    # fill missing guardian counts with 0 (market holidays = no articles that day)
    count_cols = ["trade_policy", "geopolitics", "domestic_politics"]
    df[count_cols] = df[count_cols].fillna(0).astype(int)

    return df


# ── spike detector ────────────────────────────────────────────────────────────
def add_spike_flags(df: pd.DataFrame, spike_multiplier: float = 1.0) -> pd.DataFrame:
    """
    Adds boolean spike columns for each news category.
    A spike is defined as: article_count > mean + (spike_multiplier * std)

    Parameters
    ----------
    df               : master dataframe (output of build_master_df)
    spike_multiplier : how many standard deviations above mean = spike (default 1.0)

    Returns
    -------
    df with additional columns: trade_policy_spike, geopolitics_spike,
                                domestic_politics_spike, any_spike, multi_spike
    """
    categories = ["trade_policy", "geopolitics", "domestic_politics"]

    for cat in categories:
        threshold = df[cat].mean() + spike_multiplier * df[cat].std()
        df[f"{cat}_spike"] = df[cat] > threshold

    # convenience flags for RQ4
    spike_cols = [f"{cat}_spike" for cat in categories]
    df["spike_count"]  = df[spike_cols].sum(axis=1)   # how many categories spiked
    df["any_spike"]    = df["spike_count"] >= 1
    df["multi_spike"]  = df["spike_count"] >= 2

    return df