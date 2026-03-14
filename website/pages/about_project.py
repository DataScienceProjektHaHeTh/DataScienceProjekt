import dash
from dash import html

dash.register_page(__name__, path="/about-project", name="Approach & Assumptions")

def definition_box(term, formula, description):
    return html.Div([
        html.Div("Definition", className="def-label"),
        html.Div(term, className="def-term"),
        html.Div(formula, className="def-formula"),
        html.P(description, className="def-description"),
    ], className="definition-box")

layout = html.Div([
    html.H1([
        html.Span("Approach ", className="page-h1-accent"),
        html.Span("& Assumptions", className="page-h1-main"),
    ]),
    html.P(
        "Methodology, data sources, and the formal definitions shared across all seven research questions.",
        className="page-subtitle"
    ),

    html.Section([
        html.H2("Core Definitions"),
        html.P(
            "The following terms are used consistently across all research questions. "
            "They are defined here once to avoid repetition and to make the analytical choices explicit.",
            className="section-text",
            style={"marginBottom": "1.5rem"},
        ),
        html.Div([
            definition_box(
                term="Spike Day",
                formula="spike_day  ≡  article_count > μ + 1 × σ",
                description=(
                    "A calendar day on which the article count in a given news category exceeds "
                    "the rolling 30-day mean by more than one standard deviation. "
                    "Used to identify days of unusually high coverage intensity."
                ),
            ),
            definition_box(
                term="3-Day Price Return",
                formula="r(t) = ( P_{t+3} − P_t ) / P_t × 100",
                description=(
                    "The cumulative percentage change in a daily closing price over the three "
                    "trading days following reference day t. "
                    "This is the default return window specified by the research questions; "
                    "the interactive controls on the Analysis page allow wider windows (5, 7, 14 days)."
                ),
            ),
            definition_box(
                term="Response Day",
                formula="response_day  =  argmax_{d ∈ [1,5]}  | r_cumulative(t, t+d) |",
                description=(
                    "The number of trading days between a spike day and the day within the "
                    "following 5-day window on which the cumulative return reaches its maximum "
                    "absolute value. Used in RQ6 to measure how quickly each asset class reacts "
                    "to a news shock."
                ),
            ),
            definition_box(
                term="Measurable Price Movement",
                formula="| r(t) | > 1%",
                description=(
                    "A cumulative 3-day price return exceeding ±1 % in absolute terms. "
                    "Returns below this threshold are treated as market noise and not counted "
                    "as a meaningful market response. Used as the default threshold in RQ5; "
                    "the slider on that page lets you adjust the cutoff from 0.5 % to 3 %."
                ),
            ),
        ], className="definition-grid"),
    ], className="section"),

    html.Section([
        html.H2("Datasets"),
        html.Div([
            html.Div([
                html.H3("The Guardian"),
                html.P("Articles collected via the Guardian Open Platform API using category-specific keyword queries combining 'Trump' with topic-relevant terms. Coverage begins 1 January 2025."),
            ], className="dataset-card"),
            html.Div([
                html.H3("Volume"),
                html.P("≈ 20,000 articles across three categories: Trade Policy, Geopolitics, and Domestic Politics.")
            ], className="dataset-card"),
            html.Div([
                html.H3("Content"),
                html.P("Article headline, body text (first 512 chars for VADER), publication date, and section tag.")
            ], className="dataset-card"),
        ], className="dataset-grid"),
        html.Div([
            html.Div([
                html.H3("Yahoo Finance"),
                html.P("Daily closing prices downloaded via yfinance for MSCI World ETF (URTH), Gold Futures (GC=F), and Bitcoin (BTC-USD).")
            ], className="dataset-card"),
            html.Div([
                html.H3("Period"),
                html.P("20 January 2025 (start of Trump's second term) through the data collection cut-off.")
            ], className="dataset-card"),
            html.Div([
                html.H3("Fields"),
                html.P("Open, high, low, close prices and trading volume. Resampled from hourly to daily; forward-filled on market holidays only.")
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
