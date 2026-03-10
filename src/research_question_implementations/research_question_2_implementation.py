#How do MSCI World, Gold, and Bitcoin differ in the direction and magnitude of their cumulative 3-day price returns
# following identical Trump-related news events in the Guardian across all three news categories?

#Find Spike days, that match in all news types
#cauculate the x day price return for each spike day and each asset class
#compare the price return using a grouped bar chart

import pandas as pd
import plotly.graph_objects as go
from glob import glob

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
                else:
                    print(f"Skipping spike day {date} due to proximity to last kept spike day {last_kept_date} (gap: {gap} days)")


        return filtered_spike_days

    #Intersection of all spike day lists to find shared spike days across all news categories
    shared = sorted(set.intersection(*[set(lst.index) for lst in spike_days_list]))
    print(f"Shared spike days across all news categories: {shared}")

    return remove_duplicate_spike_days(shared)

def load_price_data(filepath):
    df = pd.read_csv(filepath, skiprows=[1,2], index_col=0, parse_dates=True)

    df.index = df.index.tz_localize(None)

    daily_close = df["Close"].resample("D").last().dropna()

    return daily_close

def calculate_price_return(spike_days, daily_close, days_after = 3):

    def get_nearest_price(daily_close, date):
        for offset in range(4):  # try today, +1, +2, +3 days
            try:
                return daily_close.loc[date + pd.Timedelta(days=offset)]
            except KeyError:
                continue
        return None  # no data found within 3 days

    #calculate the normal x-day price return, to see if the price returns following the spike days are significantly different from the normal price returns
    all_returns = daily_close.pct_change(periods = days_after) * 100
    normal_returns = all_returns.mean()
    normal_std = all_returns.std()

    results = []

    for spike_day in spike_days:
        date = pd.to_datetime(spike_day)
        date_end = date + pd.Timedelta(days = days_after)

        
        price_start = daily_close.loc[date]
        price_end = get_nearest_price(daily_close, date_end)

        if price_start == None or price_end == None:
            print(f"Missing price data for spike day {spike_day} or end date {date_end}. Skipping this spike day.")
            continue

        #calculate the x-day price return as a percentage
        raw_return = (price_end - price_start) / price_start * 100
        #how much does the price return following the spike deviate from the normal x-day return?
        abnormal_return = raw_return - normal_returns

        z_score = abnormal_return / normal_std

        #add all information to the results list
        results.append({
            "date": date.strftime("%Y-%m-%d"),
            "raw_return": round(raw_return, 2),
            "abnormal_return": round(abnormal_return, 2),
            "z_score": round(z_score, 2),
            "significant": abs(z_score) > 1.3
        })

    return pd.DataFrame(results)


#-------------get all spike days for each news category----------------

#get all filepaths for the processed news data
files = glob("data/processed/articles_with_sentiment_guardian*.csv")

all_spike_days = []

for file in files:
    #read the news data for the current category into a DataFrame
    news_data = pd.read_csv(file)
    #calculate the spike days for the current news category
    spike_days = get_spike_days_of_single_class(news_data)
    #append the spike days to the list of all spike days
    all_spike_days.append(spike_days)
    print(f"Spike days for {file}: {spike_days}")

#get the shared spike days across all news categories
shared_spike_days = get_shared_spike_days(all_spike_days)

#-------------calculate price returns for the shared spike days----------------

#get all the filepaths of the price data
files = glob("data/raw/*.csv")

all_results = []

#for all investments, read the price data and calculate the price returns for the shared spike days
for file in files:

    asset_name = file.replace("data/raw/", "").replace(".csv","")

    daily_close = load_price_data(file)
    price_returns = calculate_price_return(shared_spike_days, daily_close, days_after=1)
    
    #add a column with the asset name
    price_returns["asset"] = asset_name
    all_results.append(price_returns)

df_all = pd.concat(all_results, ignore_index=True)
print(df_all)
#-----------visualize the data----------------------------

fig = go.Figure()

#get all the asset names
assets = df_all["asset"].unique()
colors = {"gold": "gold", "bitcoin": "royalblue", "msci_world": "seagreen"}

for asset in assets:
    asset_data = df_all[df_all["asset"] == asset]

    fig.add_trace(go.Bar(
        name = asset,
        x = asset_data["date"],
        y = asset_data["abnormal_return"],
        marker_color=colors.get(asset, "gray"),
        hovertemplate=(
            "<b>%{x}</b><br>" +
            "Asset: " + asset + "<br>" +
            "Abnormal Return: %{y:.2f}%<br>" +
            "Z-Score: %{customdata[0]}<br>" +
            "Significant: %{customdata[1]}" +
            "<extra></extra>"
        ),
        customdata = asset_data[["z_score", "significant"]].values
    ))

    #----------Layout----------------------------------------

    fig.update_layout(
        title = "x-Day Abnormal Returns after Trump news spikes",
        xaxis_title = "Event Date",
        yaxis_title = "Abnormal Return (%)",
        barmode="group",
        hovermode = "x unified",
        plot_bgcolor = "white",
        legend_title="Asset",
        #add a zero line
        shapes = [dict(
            type = "line", x0 = 0, x1 = 1, xref = "paper",
            y0 = 0, y1 = 0, yref = "y",
            line = dict(color = "black", width = 1, dash = "dash")
        )]
    )

    fig.show()