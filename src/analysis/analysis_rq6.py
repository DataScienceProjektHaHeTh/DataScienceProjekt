import pandas as pd
import numpy as np
from data_loader import build_master_df, add_spike_flags

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
    start_date:       str   = "2025-01-20",
    end_date:         str   = None,
    max_lag:          int   = 5,
    spike_multiplier: float = 1.0,
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
    # load data with 5-day return window so we have enough forward data
    df = build_master_df(start_date=start_date, end_date=end_date, return_window=max_lag)
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


if __name__ == "__main__":
    results = run_rq6()
    print("\n── PEAK LAG SUMMARY ──")
    print(get_peak_lag_summary(results).to_string())