import dash
from dash import html

dash.register_page(__name__, path="/about-project", name="About Project")

layout = html.Div([
    html.H1("About the Project"),

    html.Section([
        html.H2("Motivation"),
        html.P(
            "Placeholder: What motivated us to choose this topic? Why is it interesting and relevant?",
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
                html.P("Placeholder: How did we collect and source our data?")
            ])
        ], className="step"),
        html.Div([
            html.Div("2", className="step-number"),
            html.Div([
                html.H3("Data Cleaning"),
                html.P("Placeholder: How did we clean and preprocess the data?")
            ])
        ], className="step"),
        html.Div([
            html.Div("3", className="step-number"),
            html.Div([
                html.H3("Analysis"),
                html.P("Placeholder: What methods did we use? (e.g. sentiment analysis, clustering, ...)")
            ])
        ], className="step"),
        html.Div([
            html.Div("4", className="step-number"),
            html.Div([
                html.H3("Visualization"),
                html.P("Placeholder: How we you visualize our results?")
            ])
        ], className="step"),
    ], className="section"),

], className="page")