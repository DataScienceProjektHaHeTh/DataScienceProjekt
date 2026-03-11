#Research question 4:
#To what degree does the co-occurrence of spikes across multiple news categories in the Guardian on the same day
# amplify the cumulative 3-day price return compared to days with an isolated single-category spike,
# and which asset class shows the greatest sensitivity to this multi-category overlap effect?


#get spike days for single article categories
#find days that only have spikes in single category
#find days that have spikes in all categories

#calculate x day return on each investment for all found dates

#compare different returns for single and all spike

from glob import glob
import pandas as pd
import os
import sys
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from research_question_2_implementation import(
    get_spike_days_of_single_class,
    get_shared_spike_days,
    calculate_price_return,
    load_price_data
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_MARKET = os.path.join(BASE_DIR, "../../data/raw/market")
DATA_NEWS_PROCESSED = os.path.join(BASE_DIR, "../../data/processed/articles_with_sentiment")


#get all filepaths for the processed news data
paths = glob(os.path.join(DATA_NEWS_PROCESSED, "*.csv"))

def get_spike_days_of_all_category(paths):
    single_category_spike_days = []
    for path in paths:
        #get the name of the category
        category_name = os.path.basename(path).replace("_with_sentiment.csv","")
        #read the news data for the current category into a DataFrame
        news_data = pd.read_csv(path)
        #calculate the spike days for the current news category
        spike_days = get_spike_days_of_single_class(news_data)
        #append the spike days to the list of all spike days
        single_category_spike_days.append((category_name,spike_days))
    return single_category_spike_days

def get_isolated_spike_days(all_spike_days):
    #Find days that spike in EXACTLY ONE category.
    from collections import Counter

    # Count how many categories each date appears in
    all_dates = []
    for category_name, spike_days in all_spike_days:
        all_dates.extend(spike_days.index.tolist())

    date_counts = Counter(all_dates)

    # Keep only dates that appear in exactly one category
    isolated = sorted([date for date, count in date_counts.items() if count == 1])
    return isolated



#---------- calculate spike days ----------------------------
single_category_spike_days = get_spike_days_of_all_category(paths)

shared_spike_days = get_shared_spike_days([spike_days for _, spike_days in single_category_spike_days])

isolated_spike_days = get_isolated_spike_days(single_category_spike_days)

#---------- calculate returns for both single and shared spike days ----------------------------

all_daily_returns = {}

for file in glob(os.path.join(DATA_MARKET, "*.csv")):
    asset_name = os.path.basename(file).replace(".csv", "")
    all_daily_returns[asset_name] = load_price_data(file)

DAYS_AFTER = 3
results = []

for asset_name, price_data in all_daily_returns.items():

    #returns after multi-category spike days
    multi_category_returns = calculate_price_return(shared_spike_days, price_data, DAYS_AFTER)
    multi_category_returns["spike_type"] = "multi-category"
    multi_category_returns["asset"] = asset_name

    #returns after single-category spike days
    single_category_returns = calculate_price_return(isolated_spike_days, price_data, DAYS_AFTER)
    single_category_returns["spike_type"] = "single-category"
    single_category_returns["asset"] = asset_name

    results.extend([multi_category_returns, single_category_returns])

df_all = pd.concat(results, ignore_index=True)

#---- average return per asset per spike day ---------------------------------------

summary = df_all.groupby(["asset", "spike_type"])["abnormal_return_%"].agg(
    avg_return="mean",
    median_return="median",
    std_return="std",
    count="count"
).reset_index()

print(summary)

#------- Visualization --------------------------------------------------

colors = {"multi-category": "crimson", "single-category": "steelblue"}
fig = go.Figure()

for spike_type in ["single-category", "multi-category"]:
    data = summary[summary["spike_type"] == spike_type]
    fig.add_trace(go.Bar(
        name=spike_type,
        x=data["asset"],
        y=data["avg_return"],
        marker_color=colors[spike_type],
        hovertemplate=(
            f"<b>%{{x}}</b><br>" +
            f"Spike type: {spike_type}<br>" +
            "Avg abnormal return: %{y:.2f}%<extra></extra>"
        )
    ))

fig.update_layout(
    title=f"RQ4: Single vs Multi-Category News Spikes — Avg {DAYS_AFTER}-Day Abnormal Return",
    xaxis_title="Asset",
    yaxis_title="Avg Abnormal Return (%)",
    barmode="group",
    plot_bgcolor="white",
    height=500,
    legend_title="Spike Type",
    shapes=[dict(
        type="line", x0=0, x1=1, xref="paper",
        y0=0, y1=0, yref="y",
        line=dict(color="black", width=1, dash="dash")
    )]
)

#fig.show()

def build_chart_rq4(days_after):
    colors = {"multi-category": "crimson", "single-category": "steelblue"}
    fig = go.Figure()

    results = []
    for asset_name, price_data in all_daily_returns.items():
        multi = calculate_price_return(shared_spike_days, price_data, days_after)
        multi["spike_type"] = "multi-category"
        multi["asset"] = asset_name

        single = calculate_price_return(isolated_spike_days, price_data, days_after)
        single["spike_type"] = "single-category"
        single["asset"] = asset_name

        results.extend([multi, single])

    df = pd.concat(results, ignore_index=True)
    summary = df.groupby(["asset", "spike_type"])["abnormal_return_%"].mean().reset_index()
    summary.columns = ["asset", "spike_type", "avg_return"]

    for spike_type in ["single-category", "multi-category"]:
        data = summary[summary["spike_type"] == spike_type]
        fig.add_trace(go.Bar(
            name=spike_type,
            x=data["asset"],
            y=data["avg_return"],
            marker_color=colors[spike_type],
            hovertemplate=(
                "<b>%{x}</b><br>" +
                f"Spike type: {spike_type}<br>" +
                "Avg abnormal return: %{y:.2f}%<extra></extra>"
            )
        ))

    fig.update_layout(
        title=f"RQ4: Single vs Multi-Category Spikes ({days_after}-day return)",
        xaxis_title="Asset",
        yaxis_title="Avg Abnormal Return (%)",
        barmode="group",
        plot_bgcolor="white",
        height=500,
        legend_title="Spike Type",
        shapes=[dict(
            type="line", x0=0, x1=1, xref="paper",
            y0=0, y1=0, yref="y",
            line=dict(color="black", width=1, dash="dash")
        )]
    )
    return fig

def build_chart_rq4_category_breakdown(asset_name, days_after):
    """Shows returns for one asset broken down by which category combination spiked."""
    from collections import Counter
    import itertools

    colors = {
        "all categories":       "crimson",
        "domestic only":        "steelblue",
        "trade only":           "goldenrod",
        "geopolitics only":     "seagreen",
        "domestic + trade":     "mediumpurple",
        "domestic + geo":       "darkorange",
        "trade + geo":          "teal",
    }

    daily_close = all_daily_returns.get(asset_name)
    if daily_close is None:
        return go.Figure()

    # ── Build a dict: date → set of categories that spiked ───────────
    date_to_categories = {}
    for category_name, spike_days in single_category_spike_days:
        for date in spike_days.index:
            date_to_categories.setdefault(date, set()).add(category_name)

    # ── Group dates by their category combination ────────────────────
    combination_to_dates = {}
    for date, cats in date_to_categories.items():
        # Create a readable label from the set of categories
        if len(cats) == len(single_category_spike_days):
            label = "all categories"
        elif len(cats) == 1:
            cat = list(cats)[0]
            # Shorten the category name
            label = cat.replace("articles_with_sentiment_guardian_", "") + " only"
        else:
            label = " + ".join(sorted([
                c.replace("articles_with_sentiment_guardian_", "")
                for c in cats
            ]))
        combination_to_dates.setdefault(label, []).append(date)

    # ── Calculate avg return for each combination ────────────────────
    combo_results = []
    for label, dates in combination_to_dates.items():
        returns = calculate_price_return(dates, daily_close, days_after=days_after)
        if not returns.empty:
            combo_results.append({
                "combination": label,
                "avg_return":  round(returns["abnormal_return_%"].mean(), 2),
                "count":       len(returns)
            })

    df_combo = pd.DataFrame(combo_results).sort_values("avg_return", ascending=False)

    # ── Build figure ─────────────────────────────────────────────────
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_combo["combination"],
        y=df_combo["avg_return"],
        marker_color=[colors.get(c, "gray") for c in df_combo["combination"]],
        hovertemplate=(
            "<b>%{x}</b><br>" +
            "Avg abnormal return: %{y:.2f}%<br>" +
            "Events: %{customdata}<extra></extra>"
        ),
        customdata=df_combo["count"].values
    ))

    fig.update_layout(
        title=f"{asset_name}: Avg {days_after}-Day Return by News Category Combination",
        xaxis_title="News Category Combination",
        yaxis_title="Avg Abnormal Return (%)",
        plot_bgcolor="white",
        height=500,
        shapes=[dict(
            type="line", x0=0, x1=1, xref="paper",
            y0=0, y1=0, yref="y",
            line=dict(color="black", width=1, dash="dash")
        )]
    )
    return fig