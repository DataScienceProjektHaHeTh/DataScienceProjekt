#How do MSCI World, Gold, and Bitcoin differ in the direction and magnitude of their cumulative 3-day price returns
# following identical Trump-related news events in the Guardian across all three news categories?

#Find Spike days, that match in all news types
#cauculate the x day price return for each spike day and each asset class
#compare the price return using a grouped bar chart

import pandas as pd
import plotly.graph_objects as go
import os
from plotly.subplots import make_subplots
from glob import glob

#for global filepaths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_MARKET = os.path.join(BASE_DIR, "../../data/raw/market")
DATA_NEWS_PROCESSED = os.path.join(BASE_DIR, "../../data/processed/articles_with_sentiment")


def get_spike_days_of_single_class(news_data):
    #Calculate the number of articles published per day, by grouping the news data by date and counting the number of articles for each date
    articles_per_day = news_data.groupby("date").size()

    #Calculate the average and standard deviation of the number of articles per day, and define a threshold for identifying spike days as those that exceed the average by a certain number of standard deviations
    average = articles_per_day.mean()
    std_dev = articles_per_day.std()

    #adjust the sensitivity to find more or less spike days
    SENSITIVITY = 1
    threshold = average + SENSITIVITY * std_dev

    #Filter the days that exceed the threshold to get the spike days for the current news category
    filtered_spike_days = articles_per_day[articles_per_day > threshold]

    #Sort the spike days by date to ensure they are in chronological order
    filtered_spike_days = filtered_spike_days.sort_index()
    
    return filtered_spike_days

def get_shared_spike_days(spike_days_list):

    def remove_duplicate_spike_days(spike_days):

        MIN_GAP_DAYS = 5
        filtered_spike_days = []
        last_kept_date = None

        for date in spike_days:
            #always keep the first spike day
            if last_kept_date is None:
                filtered_spike_days.append(date)
                last_kept_date = date
            #for subsequent spike days, check the gap to the last kept spike day
            else:
                gap = (pd.to_datetime(date) - pd.to_datetime(last_kept_date)).days
                if gap >= MIN_GAP_DAYS:
                    filtered_spike_days.append(date)
                    last_kept_date = date   
                #else:
                    #print(f"Skipping spike day {date} due to proximity to last kept spike day {last_kept_date} (gap: {gap} days)")


        return filtered_spike_days

    #Intersection of all spike day lists to find shared spike days across all news categories
    shared = sorted(set.intersection(*[set(lst.index) for lst in spike_days_list]))
    #print(f"Shared spike days across all news categories: {shared}")

    return remove_duplicate_spike_days(shared)

def load_price_data(filepath):
    df = pd.read_csv(filepath, skiprows=[1,2], index_col=0, parse_dates=True)

    df.index = df.index.tz_localize(None)

    daily_close = df["Close"].resample("D").last().dropna()

    return daily_close

def calculate_price_return(spike_days, daily_close, days_after = 3, pre_event_days = 5):

    def get_nearest_price(daily_close, date):
        for offset in range(4):  # try today, +1, +2, +3 days
            try:
                return daily_close.loc[date + pd.Timedelta(days=offset)]
            except KeyError:
                continue
        return None  # no data found within 3 days

    results = []

    for spike_day in spike_days:
        date = pd.to_datetime(spike_day)
        date_end = date + pd.Timedelta(days = days_after)

        #get the price the day before the spike day to calculate the normal return distribution
        price_anchor = get_nearest_price(daily_close, date - pd.Timedelta(days = 1))
        price_day0 = get_nearest_price(daily_close, date)
        price_end = get_nearest_price(daily_close, date + pd.Timedelta(days = days_after))

        if any(p is None for p in [price_anchor, price_day0, price_end]):
            #print(f"⚠️ Skipping {spike_day} — missing price data")
            continue

        #calculate pre event returns to establish a normal return distribution
        pre_event_returns = []
        for d in range(1, pre_event_days + 1):
            p_start = get_nearest_price(daily_close, date - pd.Timedelta(days = d + 1))
            p_end = get_nearest_price(daily_close, date - pd.Timedelta(days = d))
            if p_start is not None and p_end is not None:
                pre_event_returns.append((p_end - p_start) / p_start * 100)
        
        expected_daily_return = sum(pre_event_returns) / len(pre_event_returns) if pre_event_returns else 0

        #calculate the normal x day return based on the expected daily return
        raw_return_day0 = (price_day0 - price_anchor) / price_anchor * 100
        raw_return_end = (price_end - price_anchor) / price_day0 * 100

        #expected total drift over the full window
        expected_total = expected_daily_return * (days_after +1)

        abnormal_return = raw_return_end - expected_total

        normal_std = daily_close.pct_change().std() * 100
        z_score = abnormal_return / normal_std if normal_std > 0 else 0

        #add all information to the results list
        results.append({
            "date":             date.strftime("%Y-%m-%d"),
            "return_day0_%":    round(raw_return_day0, 2),  #reaction on the spike day itself
            "raw_return_%":     round(raw_return_end, 2),   #total return over the full window
            "expected_drift_%": round(expected_total, 2),   #what trend would we expect based on the pre-event returns
            "abnormal_return_%":  round(abnormal_return, 2),  #above or below the expected return based on the pre-event trend
            "z_score":          round(z_score, 2),
            "significant":      abs(z_score) > 1.3
        })

    return pd.DataFrame(results)


#-------------get all spike days for each news category----------------

#get all filepaths for the processed news data
news_files_paths = glob(os.path.join(DATA_NEWS_PROCESSED, "*.csv"))

all_spike_days = []

for file_path in news_files_paths:
    #read the news data for the current category into a DataFrame
    news_data = pd.read_csv(file_path)
    #calculate the spike days for the current news category
    spike_days = get_spike_days_of_single_class(news_data)
    #append the spike days to the list of all spike days
    all_spike_days.append(spike_days)
    #print(f"Spike days for {file}: {spike_days}")

#get the shared spike days across all news categories
shared_spike_days = get_shared_spike_days(all_spike_days)

#-------------calculate price returns for the shared spike days----------------

#get all the filepaths of the price data
files = glob(os.path.join(DATA_MARKET,"*.csv"))

all_results = []

#for all investments, read the price data and calculate the price returns for the shared spike days
for file in files:

    asset_name = os.path.basename(file).replace(".csv","")

    daily_close = load_price_data(file)
    price_returns = calculate_price_return(shared_spike_days, daily_close, days_after=1)
    
    #add a column with the asset name
    price_returns["asset"] = asset_name
    all_results.append(price_returns)

df_all = pd.concat(all_results, ignore_index=True)
#print(df_all)
#-----------visualize the data---------------------------- old

def plot_chart1_abnormal_returns(shared_spike_days, all_daily_closes):
    """Grouped bar chart with dropdown to select days_after."""

    assets = list(all_daily_closes.keys())
    colors = {"gold": "gold", "bitcoin": "royalblue", "msci_world": "seagreen"}
    days_after_options = [1, 3, 5, 7]
    default_da = 3

    fig = go.Figure()
    all_trace_meta = []

    # ── Precompute returns for every days_after option ───────────────
    for da in days_after_options:

        # Recalculate df_all for this days_after value
        results_for_da = []
        for asset, daily_close in all_daily_closes.items():
            price_returns = calculate_price_return(shared_spike_days, daily_close, days_after=da)
            price_returns["asset"] = asset
            results_for_da.append(price_returns)

        df_da = pd.concat(results_for_da, ignore_index=True)

        # Add one bar trace per asset for this days_after value
        for asset in assets:
            asset_data = df_da[df_da["asset"] == asset]
            is_default = (da == default_da)

            fig.add_trace(go.Bar(
                name=asset,
                x=asset_data["date"],
                y=asset_data["abnormal_return_%"],
                marker_color=colors.get(asset, "gray"),
                visible=is_default,
                legendgroup=asset,
                showlegend=is_default,  # only show legend for default
                hovertemplate=(
                    "<b>%{x}</b><br>" +
                    f"Asset: {asset}<br>" +
                    "Abnormal Return: %{y:.2f}%<br>" +
                    "Z-Score: %{customdata[0]}<br>" +
                    "Significant: %{customdata[1]}<extra></extra>"
                ),
                customdata=asset_data[["z_score", "significant"]].values
            ))

            all_trace_meta.append({"da": da, "asset": asset})

    # ── Visibility helper ────────────────────────────────────────────
    def make_visibility(sel_da):
        return [m["da"] == sel_da for m in all_trace_meta]

    # ── Dropdown buttons ─────────────────────────────────────────────
    da_buttons = [
        dict(
            label=f"{da} days after",
            method="update",
            args=[
                {"visible": make_visibility(da),
                 # update legend: only show for selected da
                 "showlegend": [m["da"] == da for m in all_trace_meta]},
                {"title": f"RQ2: Abnormal Returns ({da} days after event)"}
            ]
        )
        for da in days_after_options
    ]

    # ── Layout ───────────────────────────────────────────────────────
    fig.update_layout(
        title=f"RQ2: Abnormal Returns ({default_da} days after event)",
        xaxis_title="Event Date",
        yaxis_title="Abnormal Return (%)",
        barmode="group",
        hovermode="x unified",
        plot_bgcolor="white",
        height=550,
        legend_title="Asset",
        shapes=[dict(
            type="line", x0=0, x1=1, xref="paper",
            y0=0, y1=0, yref="y",
            line=dict(color="black", width=1, dash="dash")
        )],
        updatemenus=[
            dict(
                buttons=da_buttons,
                direction="down",
                x=0.0, y=1.15, xanchor="left",
                showactive=True,
                bgcolor="lightgreen",
                bordercolor="gray",
            )
        ],
        annotations=[
            dict(text="➡️ Days after event:", x=0.0, y=1.19,
                 xref="paper", yref="paper", showarrow=False)
        ]
    )

    fig.write_html("data/processed/rq2_chart1_abnormal_returns.html")
    fig.show()


def plot_chart2_event_window(shared_spike_days, all_daily_closes):
    """Price path around a selected event with dropdowns for event, days before/after."""

    colors = {"gold": "gold", "bitcoin": "royalblue", "msci_world": "seagreen"}

    days_before_options = [3, 5, 7, 10]
    days_after_options  = [3, 5, 7, 10]
    event_options       = shared_spike_days

    default_event = event_options[0]
    default_db    = days_before_options[1]  # 5
    default_da    = days_after_options[1]   # 5

    fig = go.Figure()

    # ── Precompute all traces ────────────────────────────────────────
    all_trace_meta = []

    for event in event_options:
        for db in days_before_options:
            for da in days_after_options:
                for asset, daily_close in all_daily_closes.items():

                    date = pd.to_datetime(event)
                    path = []

                    for offset in range(-db, da + 1):
                        target = date + pd.Timedelta(days=offset)
                        price = None
                        for adj in range(4):
                            try:
                                price = daily_close.loc[target + pd.Timedelta(days=adj)]
                                break
                            except KeyError:
                                continue
                        path.append(price)

                    path = [p if p is not None else float("nan") for p in path]
                    anchor = path[db - 1] if path[db - 1] else 1
                    path_norm = [(p / anchor) * 100 if p else float("nan") for p in path]

                    is_default = (event == default_event and db == default_db and da == default_da)

                    fig.add_trace(go.Scatter(
                        name=asset,
                        x=list(range(-db, da + 1)),
                        y=path_norm,
                        mode="lines+markers",
                        line=dict(color=colors.get(asset, "gray"), width=2),
                        marker=dict(size=6),
                        visible=is_default,
                        hovertemplate=f"<b>{asset}</b><br>Day: %{{x}}<br>Price (norm): %{{y:.2f}}<extra></extra>"
                    ))

                    all_trace_meta.append({
                        "event": event, "db": db, "da": da, "asset": asset
                    })

    # ── Visibility helper ────────────────────────────────────────────
    def make_visibility(sel_event, sel_db, sel_da):
        return [
            m["event"] == sel_event and m["db"] == sel_db and m["da"] == sel_da
            for m in all_trace_meta
        ]

    # ── Dropdown buttons ─────────────────────────────────────────────
    event_buttons = [
        dict(label=str(e), method="update",
             args=[{"visible": make_visibility(e, default_db, default_da)},
                   {"title": f"Price Path Around Event: {e}"}])
        for e in event_options
    ]

    db_buttons = [
        dict(label=f"{db} days before", method="update",
             args=[{"visible": make_visibility(default_event, db, default_da)}])
        for db in days_before_options
    ]

    da_buttons = [
        dict(label=f"{da} days after", method="update",
             args=[{"visible": make_visibility(default_event, default_db, da)}])
        for da in days_after_options
    ]

    # ── Layout ───────────────────────────────────────────────────────
    fig.update_layout(
        title=f"Price Path Around Event: {default_event}",
        xaxis_title="Days relative to news spike (0 = news day)",
        yaxis_title="Normalized Price (day -1 = 100)",
        hovermode="x unified",
        plot_bgcolor="white",
        height=550,
        legend_title="Asset",
        updatemenus=[
            dict(buttons=event_buttons, direction="down",
                 x=0.0, y=1.18, xanchor="left",
                 showactive=True, bgcolor="lightblue"),
            dict(buttons=db_buttons, direction="down",
                 x=0.35, y=1.18, xanchor="left",
                 showactive=True, bgcolor="lightyellow"),
            dict(buttons=da_buttons, direction="down",
                 x=0.65, y=1.18, xanchor="left",
                 showactive=True, bgcolor="lightgreen"),
        ],
        annotations=[
            dict(text="📅 Event:",       x=0.0,  y=1.22, xref="paper", yref="paper", showarrow=False),
            dict(text="⬅️ Days before:", x=0.35, y=1.22, xref="paper", yref="paper", showarrow=False),
            dict(text="➡️ Days after:",  x=0.65, y=1.22, xref="paper", yref="paper", showarrow=False),
        ]
    )

    fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="📰 News")
    fig.add_hline(y=100, line_dash="dot", line_color="gray")

    fig.write_html("data/processed/rq2_chart2_event_window.html")
    fig.show()

all_daily_closes = {}

for file in glob(os.path.join(DATA_MARKET,"*.csv")):
    asset_name = os.path.basename(file).replace(".csv", "")
    all_daily_closes[asset_name] = load_price_data(file)


# ── Call both ────────────────────────────────────────────────────────
#plot_chart1_abnormal_returns(shared_spike_days, all_daily_closes)
#plot_chart2_event_window(shared_spike_days, all_daily_closes)

#---functions for the Website-------------------------

#build the first chart with the option to select the days after the event
def build_chart1(days_after):
    colors = {"gold": "gold", "bitcoin": "royalblue", "msci_world": "seagreen"}
    #create a bar chart with plotly, with one bar per asset, showing the abnormal return for each shared spike day, with a dropdown to select the days after the event
    fig = go.Figure()
    for asset, daily_close in all_daily_closes.items():
        df = calculate_price_return(shared_spike_days, daily_close, days_after=days_after)
        fig.add_trace(go.Bar(
            name=asset,
            x=df["date"],
            y=df["abnormal_return_%"],
            marker_color=colors.get(asset, "gray"),
            customdata=df[["z_score", "significant"]].values,
            hovertemplate=(
                "<b>%{x}</b><br>" + f"Asset: {asset}<br>" +
                "Abnormal Return: %{y:.2f}%<br>" +
                "Z-Score: %{customdata[0]}<br>" +
                "Significant: %{customdata[1]}<extra></extra>"
            )
        ))
    fig.update_layout(
        title=f"Abnormal Returns ({days_after} days after event)",
        barmode="group", hovermode="x unified",
        plot_bgcolor="white", height=500
    )
    return fig

#build the second chart with the option to select the event and the days before and after the event
def build_chart2(event, days_before, days_after):
    import pandas as pd
    colors = {"gold": "gold", "bitcoin": "royalblue", "msci_world": "seagreen"}
    fig = go.Figure()
    date = pd.to_datetime(event)
    for asset, daily_close in all_daily_closes.items():
        path = []
        for offset in range(-days_before, days_after + 1):
            target = date + pd.Timedelta(days=offset)
            price = None
            for adj in range(4):
                try:
                    price = daily_close.loc[target + pd.Timedelta(days=adj)]
                    break
                except KeyError:
                    continue
            path.append(price if price is not None else float("nan"))
        anchor = path[days_before - 1] or 1
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
        plot_bgcolor="white", height=500
    )
    fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="📰 News")
    fig.add_hline(y=100, line_dash="dot", line_color="gray")
    return fig