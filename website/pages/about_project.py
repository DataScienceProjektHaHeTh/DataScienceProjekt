import dash
from dash import html

dash.register_page(__name__, path="/about-project", name="About Project")

layout = html.Div([
    html.H1("About the Project"),

    html.Section([
        html.H2("Motivation"),
        html.P(
            "Donald Trump's second presidency has been marked ba an unusually high pace of politically consequential decisions: sweeping tariff announcements, shifts in Nato commitments, executive orders targeting federal agencies, and ongoing geopolitical crises. Each of these events generate a wave of media coverage and often a visible reaction in financial markets. \n But the relationship between political news and asset prices is rarely straightforward and in our minds just a thought thats hasn't been investigated. Does more coverage move markets, or does it just create noise? Does negative news reliably send prices down? Do different asset classes react in the same way or are there different patterns to be seen? \n We chose this topic because is sits at the intersection of three trends that define the current moment: an unusually media intensive presidency, an era of very high participation in financial markets and the growing role of alternative assets like Bitcoin.",
            className="section-text"
        ),
    ], className="section"),

    #RQs
    html.Section([
        html.H2("Goals & Research Questions"),
        html.P("This project aims to answer the following research questions:"),
        html.Ul([
            html.Li("RQ1: To what extent does the daily frequency of Trump-related news coverage in the guardian, categorized by topic (trade policy, geopolitics, domestic politics), correlate with cumulative 3-day price return of MSCI World, Gold, and Bitcoin following a coverage spike?"),
            html.Li("RQ2: How do MSCI World, Gold, and Bitcoin differ in the direction and magnitude of their cumulative 3-day price returns following identical Trump-related news events in the Guardian across all three news categories?"),
            html.Li("RQ3: How does the average daily sentiment score of Trump-related Guardian articles within each news category relate to the direction and magnitude of the cumulative 3-day price return across all three asset classes?"),
            html.Li("RQ4: To what degree does the co-occurrence of spikes across multiple news categories in the Guardian on the same day amplify the cumulative 3-day price return compared to days with an isolated single-category spike, and which asset class shows the greatest sensitivity to this multi-category overlap effect?"),
            html.Li("RQ5: Above which daily article volume threshold per news category does a measurable cumulative 3-day price return exceeding 1% first consistently appear across MSCI World, Gold, and Bitcoin, and how does this threshold differ between the three news categories?"),
            html.Li("RQ6: Within a 5-day window following a Trump-related Guardian coverage spike, how does the average price response lag to peak cumulative return differ across trade policy, geopolitics, and domestic politics – and which asset class (MSCI World, Gold, Bitcoin) consistently reaches its peak return fastest?"),
            html.Li("RQ7: Which of the three news categories (trade policy, geopolitics, domestic politics) generates the highest average daily article volume in the Guardian during Trump's current legislative period, and how does the ranking by coverage volume compare to the ranking by strength of correlation with cumulative 3-day price returns across MSCI World, Gold, and Bitcoin?"),
        ], className="rq-list"),
    ], className="section"),


    html.Section([
        html.H2("Continuous Definitions within the RQs"),
        html.Ul([
            html.Li("pike:=  spike_day = article_count > (mean + 1 * std_deviation)"),
            html.Li("3-day price return:= return = (close_day+3 - close_day0) / close_day0 * 100"),
            html.Li("response day:= number of trading days between a spike day and the day within the following 5-day window where the cumulative price return reaches its maximum absolute value"),
            html.Li("Measurable price movement:= A cumulative 3-day price return exceeding ±1% in absolute terms. Movements below this threshold are treated as market noise and not counted as a meaningful response.")
    ], className="rq-list"),
    ], className="Continious definitions within the RQs"),


    #balance Text length better
    html.Section([
        html.H2("Datasets"),
        html.Div([
            html.Div([
                html.H3("The Guardian"),
                html.P("The articles were collected using the Guardian Open Platform API, which provides access to their news content. We focused on articles published since the start of the second term that contained Trump-related keywords."),
            ], className="dataset-card"),
            html.Div([
                html.H3("Size"),
                html.P("We get around 20.000 articles from the Guardian API")
            ], className="dataset-card"),
            html.Div([
                html.H3("Type"),
                html.P("Here we have the text data of the articles, including metadata such as publication date, etc..")
            ], className="dataset-card"),
        ], className="dataset-grid"),
        html.Div([
            html.Div([
                html.H3("Yahoo Finance"),
                html.P("The market data was collected using the Yahoo Finance API, which provides historical price data for various financial investments.")
            ], className="dataset-card"),
            html.Div([
                html.H3("Size"),
                html.P("We collected hourly price data for MSCI World, Gold, and Bitcoin from the start of Trump's second term until the end of our data collection period.")
            ], className="dataset-card"),
            html.Div([
                html.H3("Type"),
                html.P("Here we have the historical price data for our three selected asset classes, including open, close, high, low prices, and trading volume.")
            ], className="dataset-card"),
        ], className="dataset-grid"),
    ], className="section"),

    html.Section([
        html.H2("Methodology"),
        html.Div([
            html.Div("1", className="step-number"),
            html.Div([
                html.H3("Data Collection"),
                html.P("Guardian articles were fetched using the Guardian Open Platform API with category-specific keyword queries combining 'Trump' with terms relevant to trade policy (tariffs, WTO, USMCA), geopolitics (NATO, Ukraine, China, Taiwan), and domestic politics (executive orders, DOGE, immigration). All articles published from 1 January 2025 onward were collected, yielding approximately 20,000 articles across the three categories. Market data — hourly closing prices for the MSCI World ETF (URTH), Gold Futures (GC=F), and Bitcoin (BTC-USD) — was downloaded via the Yahoo Finance API (yfinance) and resampled to daily closing prices.")
            ])
        ], className="step"),
        html.Div([
            html.Div("2", className="step-number"),
            html.Div([
                html.H3("Data Cleaning"),
                html.P("Guardian publication timestamps were truncated to calendar dates and articles were counted per day per category. Missing days (market holidays with no articles) were filled with zero. Market prices were forward-filled only where strictly necessary to maintain a consistent daily index. For sentiment analysis, article body text was trimmed to the first 512 characters before scoring to avoid memory issues with longer texts. A rolling 30-day z-score normalisation was applied to article counts to correct for the steady upward trend in coverage volume over the study period — without this step, a day with 40 articles in January appears comparable to a day with 40 articles in October, even though the latter was unremarkable given the higher baseline.")
            ])
        ], className="step"),
        html.Div([
            html.Div("3", className="step-number"),
            html.Div([
                html.H3("Analysis"),
                html.P("Seven research questions were answered using four analytical approaches. Correlation analysis (RQ1, RQ7) used Spearman rank correlation between daily article counts and forward returns on spike days. Event-study analysis (RQ2, RQ4) computed abnormal returns — the difference between actual and trend-predicted returns — around each spike event, enabling comparison of single-category versus multi-category spikes and across asset classes. Sentiment analysis (RQ3) applied the VADER library to compute a daily average compound score per category, then correlated scores with returns and compared mean returns across negative, neutral, and positive sentiment buckets. Threshold and lag analysis (RQ5, RQ6) binned days by article count to find the volume at which measurable market reactions first consistently appear, and tracked cumulative post-spike returns over a 5-day window to identify how quickly each asset reaches its peak response.")
            ])
        ], className="step"),
        html.Div([
            html.Div("4", className="step-number"),
            html.Div([
                html.H3("Visualization"),
                html.P("All visualizations are built with Plotly and served through a Dash multi-page web application. Every chart is interactive and tied to parameter controls (return window, spike threshold, sentiment cutoffs, lag window) so readers can explore how methodological assumptions affect the results. The key distinction between the 'default' configuration — which matches the literal specification of each research question — and the 'improved' configuration (7-day return window, z-score normalisation) is shown side by side throughout, making the sensitivity of our findings to analytical choices transparent and reproducible.")
            ])
        ], className="step"),
    ], className="section"),

], className="page")