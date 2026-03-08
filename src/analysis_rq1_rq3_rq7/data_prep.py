"""
data_prep.py
============
Shared data preparation for RQ1, RQ3, and RQ7.

Outputs saved to data/processed/:
  article_counts.csv   — daily article count per category
  daily_sentiment.csv  — daily average VADER compound score per category
  market_daily.csv     — daily closing prices for all three assets
  returns_3d.csv       — 3-day forward returns for all three assets
  master.csv           — full merged DataFrame (all of the above + spike flags)
"""

import json
import pandas as pd
from pathlib import Path


# ── Paths ──────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[2]   # project root
RAW  = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"

PROC.mkdir(parents=True, exist_ok=True)

CATEGORIES = ["trade_policy", "geopolitics", "domestic_politics"]
ASSETS     = ["msci_world", "gold", "bitcoin"]


# ── Step 1: Article counts ─────────────────────────────────────────────────────

def load_article_counts() -> pd.DataFrame:
    """
    Load each guardian JSON file and count articles per calendar day per category.

    The Guardian API returns one article object per item with a 'webPublicationDate'
    field in ISO-8601 format (e.g. '2025-01-15T10:30:00Z'). We slice the first 10
    characters to get just the date string 'YYYY-MM-DD', then count how many articles
    fall on each date for each category.

    Returns a DataFrame indexed by date with columns:
        trade_policy_count, geopolitics_count, domestic_politics_count
    All missing dates (days with zero articles) are filled with 0.
    """
    frames = []
    for cat in CATEGORIES:
        path = RAW / f"guardian_{cat}.json"
        with open(path, "r") as f:
            articles = json.load(f)

        dates = [a["webPublicationDate"][:10] for a in articles]
        counts = pd.Series(dates).value_counts().rename(f"{cat}_count")
        frames.append(counts)

    df = pd.concat(frames, axis=1).fillna(0).astype(int)
    df.index = pd.to_datetime(df.index)
    df.index.name = "date"
    df.sort_index(inplace=True)
    return df


# ── Step 2: Daily sentiment ────────────────────────────────────────────────────

def load_daily_sentiment() -> pd.DataFrame | None:
    """
    Load the processed sentiment CSVs produced by sentiment.py and compute the
    average VADER compound score per calendar day per category.

    The compound score ranges from -1.0 (most negative) to +1.0 (most positive).
    Averaging it per day gives a single number that summarises how positive or
    negative Guardian coverage was on that day within each category.

    Returns None with a warning if the sentiment files haven't been generated yet
    (i.e. if sentiment.py has not been run). In that case the master DataFrame
    will simply not contain sentiment columns — all other analysis still works.
    """
    frames = []
    for cat in CATEGORIES:
        path = PROC / f"articles_with_sentiment_guardian_{cat}.csv"
        if not path.exists():
            print(f"[WARN] Sentiment file missing: {path.name} — run sentiment.py first")
            return None

        df = pd.read_csv(path, parse_dates=["date"])
        daily = df.groupby("date")["compound"].mean().rename(f"{cat}_sentiment")
        frames.append(daily)

    out = pd.concat(frames, axis=1)
    out.index.name = "date"
    out.sort_index(inplace=True)
    return out


# ── Step 3: Market daily close prices ─────────────────────────────────────────

def load_market_daily() -> pd.DataFrame:
    """
    Load hourly market CSVs from yfinance and resample to one closing price per day.

    The yfinance CSV has a 3-row header produced by pandas MultiIndex:
      Row 0: price type labels  (Close, High, Low, Open, Volume)
      Row 1: ticker labels      (URTH, URTH, ...)
      Row 2: index name label   (Datetime)
    skiprows=[1, 2] drops rows 1 and 2, leaving row 0 as the column header.
    index_col=0 makes the timestamp column the index.

    Resampling rule 'D' groups all hourly rows within a calendar day and takes
    the last available Close price — that is the daily closing price.

    For MSCI World and Gold this produces only trading days (no weekend rows).
    For Bitcoin this produces every calendar day since it trades 24/7.
    Both are correct: the 3-day return formula (shift by -3 rows) naturally
    respects each asset's trading calendar.

    Returns a DataFrame indexed by date with columns:
        msci_world_close, gold_close, bitcoin_close
    """
    frames = []
    for asset in ASSETS:
        path = RAW / f"{asset}_raw.csv"
        df = pd.read_csv(path, skiprows=[1, 2], index_col=0, parse_dates=True)
        df.index.name = "datetime"

        # Convert UTC-aware timestamps to plain date for grouping
        if df.index.tz is not None:
            df.index = df.index.tz_convert("UTC")

        daily_close = df["Close"].resample("D").last().dropna()
        daily_close.index = daily_close.index.normalize().tz_localize(None)  # strip time & tz
        daily_close.name = f"{asset}_close"
        frames.append(daily_close)

    out = pd.concat(frames, axis=1)
    out.index.name = "date"
    out.sort_index(inplace=True)
    return out


# ── Step 4: 3-day forward returns ─────────────────────────────────────────────

def compute_3d_returns(market_daily: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the cumulative 3-day price return for each asset.

    Formula (from the project definition):
        return_t = (close_{t+3} - close_t) / close_t * 100

    shift(-3) shifts the close price series 3 rows *backward in time* so that
    each row now holds the close price that will exist 3 rows later.
    Subtracting the current close and dividing gives the percentage return.

    For MSCI World and Gold the daily series contains only trading days, so
    shift(-3) equals 3 *trading days* forward — matching the project definition.
    For Bitcoin the daily series contains every calendar day, so shift(-3)
    equals 3 *calendar days* forward — also matching the definition.

    The last 3 rows of each asset will have NaN returns because there is no
    future data to compute them against. This is expected and harmless.

    Returns a DataFrame with columns:
        msci_world_3d_return, gold_3d_return, bitcoin_3d_return
    """
    returns = pd.DataFrame(index=market_daily.index)
    for asset in ASSETS:
        # dropna() isolates only this asset's own trading days before shifting,
        # so shift(-3) advances 3 rows within the asset's own calendar — not 3
        # calendar days in the unified index (which would land on weekends for
        # MSCI/Gold and produce spurious NaN values).
        close = market_daily[f"{asset}_close"].dropna()
        future_close = close.shift(-3)
        asset_returns = (future_close - close) / close * 100
        returns[f"{asset}_3d_return"] = asset_returns  # reindexes to full index automatically
    return returns


# ── Step 5: Spike flags ────────────────────────────────────────────────────────

def compute_spikes(article_counts: pd.DataFrame, threshold: float = 1.0) -> pd.DataFrame:
    """
    Mark whether each day is a spike day for each category.

    Project definition: spike_day = article_count > (mean + threshold * std_deviation)
    The default threshold of 1.0 matches the project specification. Exposing it as
    a parameter lets the website slider vary it interactively (e.g. 0.5 = more
    sensitive, 2.0 = only extreme spikes).

    Returns a boolean DataFrame with columns:
        trade_policy_spike, geopolitics_spike, domestic_politics_spike
    """
    spikes = pd.DataFrame(index=article_counts.index)
    for cat in CATEGORIES:
        col = f"{cat}_count"
        mean = article_counts[col].mean()
        std  = article_counts[col].std()
        spikes[f"{cat}_spike"] = article_counts[col] > (mean + threshold * std)
    return spikes


# ── Website helper: base data without spike flags ──────────────────────────────

def load_base_data() -> tuple:
    """
    Load and return the four base DataFrames without merging or computing spikes.
    Intended for the website: load once, then call build_master_dynamic() on each
    callback with the current slider value for threshold.

    Returns: (counts, market, returns, sentiment)
      counts    — daily article counts per category
      market    — daily close prices per asset
      returns   — 3-day forward returns per asset
      sentiment — daily avg VADER compound per category (or None)
    """
    counts    = load_article_counts()
    sentiment = load_daily_sentiment()
    market    = load_market_daily()
    returns   = compute_3d_returns(market)
    return counts, market, returns, sentiment


def build_master_dynamic(
    counts: pd.DataFrame,
    market: pd.DataFrame,
    returns: pd.DataFrame,
    sentiment: pd.DataFrame | None,
    threshold: float = 1.0,
) -> pd.DataFrame:
    """
    Assemble the master DataFrame from pre-loaded components with a given spike
    threshold. Called by Dash callbacks so the website never re-reads files from
    disk on each interaction — only the spike computation and join are repeated.
    """
    spikes = compute_spikes(counts, threshold=threshold)
    master = counts.join(spikes, how="left").join(market, how="left").join(returns, how="left")
    if sentiment is not None:
        master = master.join(sentiment, how="left")
    return master


# ── Step 6: Build and save master DataFrame ────────────────────────────────────

def build_master() -> pd.DataFrame:
    """
    Orchestrates all loading and transformation steps and joins them into a
    single master DataFrame. Saves each intermediate table as well as the
    master to data/processed/.

    The join strategy is LEFT join starting from article_counts, meaning every
    day that has at least one Guardian article is kept. Market data is aligned
    on the same date index; days where markets were closed will be NaN in the
    market and return columns.
    """
    print("Loading article counts...")
    counts = load_article_counts()

    print("Loading sentiment scores...")
    sentiment = load_daily_sentiment()

    print("Loading market prices...")
    market = load_market_daily()

    print("Computing 3-day returns...")
    returns = compute_3d_returns(market)

    print("Computing spike flags...")
    spikes = compute_spikes(counts)

    # Build master: start from counts, left-join everything else
    master = (
        counts
        .join(spikes,   how="left")
        .join(market,   how="left")
        .join(returns,  how="left")
    )

    if sentiment is not None:
        master = master.join(sentiment, how="left")

    print(f"\nMaster DataFrame: {master.shape[0]} rows x {master.shape[1]} columns")
    print(f"Date range: {master.index.min().date()} to {master.index.max().date()}")

    # Save intermediates
    counts.to_csv(PROC / "article_counts.csv")
    market.to_csv(PROC / "market_daily.csv")
    returns.to_csv(PROC / "returns_3d.csv")
    if sentiment is not None:
        sentiment.to_csv(PROC / "daily_sentiment.csv")
    master.to_csv(PROC / "master.csv")

    print("Saved all processed files to data/processed/")
    return master


if __name__ == "__main__":
    master = build_master()
    print("\nPreview:")
    print(master.head(10).to_string())
    print("\nColumn summary:")
    print(master.describe().round(4).to_string())
