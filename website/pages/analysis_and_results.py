import dash
import sys
import os
from dash import html, dcc, callback, Output, Input, ctx
import plotly.graph_objects as go

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

try:
    from src.analysis_rq1_rq3_rq7.rq2_spikedays import (
        calculate_price_return, load_price_data,
        shared_spike_days, all_daily_closes,
        build_chart1, build_chart2, build_chart3
    )
    _rq2_available = True
except Exception as e:
    print(f"[WARN] RQ2 data unavailable: {e}")
    shared_spike_days = []
    _rq2_available = False
    def build_chart1(*a, **kw): return go.Figure()
    def build_chart2(*a, **kw): return go.Figure()

try:
    from src.analysis_rq1_rq3_rq7.rq4_spikedays import (
        build_chart_rq4,
        build_chart_rq4_category_breakdown,
        all_daily_returns
    )
    _rq4_available = True
except Exception as e:
    print(f"[WARN] RQ4 data unavailable: {e}")
    _rq4_available = False
    def build_chart_rq4(*a, **kw): return go.Figure()
    def build_chart_rq4_category_breakdown(*a, **kw): return go.Figure()


from src.analysis_rq1_rq3_rq7.data_prep import (
    load_base_data, build_master_dynamic, compute_3d_returns, compute_normalized_counts,
)
from src.analysis_rq1_rq3_rq7.plots import (
    fig_rq1_heatmap, fig_rq1_scatter, fig_rq7_overview,
    fig_rq3_violin, fig_rq3_buckets,
)

try:
    from src.analysis.data_loader import load_master_from_processed
    from src.analysis.analysis_rq5 import fig_rq5_bins, fig_rq5_threshold_summary
    from src.analysis.analysis_rq6 import fig_rq6_lag_profiles, fig_rq6_peak_heatmap
    _df_rq5 = load_master_from_processed("master_rq5.csv")
    _df_rq6 = load_master_from_processed("master_rq6.csv")
    _rq56_available = True
except Exception as e:
    print(f"[WARN] RQ5/6 data unavailable: {e}")
    _rq56_available = False
    _df_rq5 = _df_rq6 = None
    def fig_rq5_bins(*a, **kw):              return go.Figure()
    def fig_rq5_threshold_summary(*a, **kw): return go.Figure()
    def fig_rq6_lag_profiles(*a, **kw):      return go.Figure()
    def fig_rq6_peak_heatmap(*a, **kw):      return go.Figure()

# Load base data once at startup — callbacks reuse this without re-reading files
_counts, _market, _returns_default, _sentiment = load_base_data()

dash.register_page(__name__, path="/visualizations", name="Analysis & Results")

RQS = ["rq1", "rq2", "rq3", "rq4", "rq5", "rq6", "rq7"]
_SHOW = {"display": "block"}
_HIDE = {"display": "none"}

RQ_OPTIONS = [
    {"label": "RQ1 — News Frequency & Market Returns",   "value": "rq1"},
    {"label": "RQ2 — Asset Response to News Spikes",     "value": "rq2"},
    {"label": "RQ3 — Sentiment vs Returns",              "value": "rq3"},
    {"label": "RQ4 — Multi-Category Spike Amplification","value": "rq4"},
    {"label": "RQ5 — Article Volume Threshold",          "value": "rq5"},
    {"label": "RQ6 — Asset Reaction Speed",              "value": "rq6"},
    {"label": "RQ7 — Volume vs Correlation Ranking",     "value": "rq7"},
]

RQ_TOOLTIPS = {
    "rq1": "Does daily news frequency, split by topic, correlate with 3-day returns in MSCI World, Gold, and Bitcoin following a coverage spike?",
    "rq2": "How do MSCI World, Gold, and Bitcoin differ in direction and magnitude of abnormal returns following identical news spikes?",
    "rq3": "Does the average daily VADER sentiment score of Guardian articles predict the direction and magnitude of 3-day returns across assets?",
    "rq4": "Do simultaneous spikes across multiple news categories amplify 3-day returns compared to isolated single-category spikes?",
    "rq5": "Above which daily article volume does a return exceeding 1% first consistently appear — and does this threshold differ by category?",
    "rq6": "Within a 5-day post-spike window, how quickly does each asset reach its peak return — and does the lag differ across news categories?",
    "rq7": "Which category generates the most daily coverage — and does the volume ranking match the ranking by correlation strength with asset returns?",
}

# ── Placeholder figure helper ──────────────────────────────────────────────────
def placeholder_fig(title="Your chart will appear here"):
    fig = go.Figure()
    fig.add_annotation(
        text=f"📊 {title}",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=18, color="#aaa"),
    )
    fig.update_layout(
        plot_bgcolor="#f8f9fa",
        paper_bgcolor="#f8f9fa",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(t=40, b=20, l=20, r=20),
        height=350,
    )
    return fig

# ── RQ2/4 dropdown options ───────────────────────────────────────────────────────
EVENT_OPTIONS           = [{"label": str(e), "value": str(e)} for e in shared_spike_days]
DAYS_AFTER_OPTIONS      = [{"label": f"{d} days after",  "value": d} for d in [1, 3, 5, 7]]
DAYS_BEFORE_OPTIONS     = [{"label": f"{d} days before", "value": d} for d in [3, 5, 7, 10]]
INVESTMENT_CLASSES       = [{"label": a, "value": a} for a in all_daily_returns.keys()]


# ── Layout ─────────────────────────────────────────────────────────────────────
layout = html.Div([
    html.H1([
        html.Span("Analysis ", className="page-h1-accent"),
        html.Span("& Results", className="page-h1-main"),
    ]),
    html.P(
        "Select a research question to explore its analysis, interactive charts, and interpretation.",
        className="page-subtitle"
    ),

    # ── RQ selector buttons ───────────────────────────────────────────────────
    html.Div([
        *[html.Button(
            rq.upper(),
            id=f"rq-btn-{rq}",
            className="rq-btn",
            title=RQ_TOOLTIPS[rq],
            n_clicks=0,
        ) for rq in RQS],
        # Hidden dropdown keeps state; callbacks still use its value
        dcc.Dropdown(
            id="rq-selector", options=RQ_OPTIONS, value="rq1",
            clearable=False, style={"display": "none"},
        ),
    ], className="rq-btn-bar"),

    # ── RQ 1 ──────────────────────────────────────────────────────────────────
    html.Div(html.Section([
        html.H2([html.Span("RQ1", className="rq-section-number"), html.Span(" — Does daily news frequency, split by topic, correlate with 3-day returns in MSCI World, Gold, and Bitcoin following a coverage spike?", className="rq-section-title-text")]),
        html.P("Spearman correlation between article spike days and forward returns for MSCI World, Gold, and Bitcoin. Adjust the parameters below to explore how assumptions affect the results."),

        html.Div([
            html.H3("Correlation Heatmap"),
            html.Div([
                html.Div([
                    html.Label("Return window (days)"),
                    dcc.Dropdown(
                        id="rq1-window",
                        options=[{"label": f"{d} days", "value": d} for d in [3, 5, 7, 10, 14]],
                        value=7,
                        clearable=False,
                        className="dropdown",
                    ),
                ], style={"width": "180px"}),
                html.Div([
                    html.Label("Spike threshold (× std)"),
                    dcc.Slider(
                        id="rq1-threshold",
                        min=0.5, max=3.0, step=0.25, value=1.0,
                        marks={v: str(v) for v in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]},
                    ),
                ], style={"width": "320px"}),
                html.Div([
                    html.Label("Count normalisation"),
                    dcc.RadioItems(
                        id="rq1-normalize",
                        options=[{"label": "Raw count", "value": "raw"}, {"label": "Z-score (30d)", "value": "zscore"}],
                        value="zscore",
                        inline=True,
                        style={"marginTop": "6px"},
                    ),
                ], style={"width": "260px"}),
            ], style={"display": "flex", "gap": "30px", "alignItems": "flex-end", "marginBottom": "16px"}),
            dcc.Graph(id="rq1-heatmap"),
            html.P(
                "Takeaway: With a 3-day window and raw article counts, no statistically significant correlation emerges across any category–asset pair. "
                "Switching to a 7-day window with z-score normalisation reveals a strong, significant flight-to-safety pattern — but exclusively in Trade Policy: "
                "MSCI World (r = −0.45, p < 0.001) and Bitcoin (r = −0.38, p = 0.002) fall while Gold rises (r = +0.40, p = 0.001) following a spike. "
                "Geopolitics and Domestic Politics remain statistically insignificant under all parameter configurations, suggesting that only trade-specific news has a direct and measurable market impact.",
                style={"backgroundColor": "#f0f4f8", "padding": "12px 16px", "borderLeft": "3px solid #4a9eda",
                       "fontSize": "13px", "color": "#444", "marginTop": "12px"},
            ),
        ], className="viz-box"),

        html.Div([
            html.H3("Scatter Grid — Spike Days"),
            html.P("Same parameters as above apply.", style={"color": "#888", "fontSize": "13px"}),
            dcc.Graph(id="rq1-scatter"),
            html.P(
                "Takeaway: The scatter confirms the heatmap signal. In the 7-day / z-score configuration, Trade Policy spike days show a clear negative trend line for MSCI World and Bitcoin "
                "and a positive one for Gold — the annotated r values in each subplot quantify this. "
                "Geopolitics and Domestic Politics produce near-flat or noisy trend lines with no consistent direction across assets, "
                "even at stricter spike thresholds (2× std) that isolate only the most extreme news days.",
                style={"backgroundColor": "#f0f4f8", "padding": "12px 16px", "borderLeft": "3px solid #4a9eda",
                       "fontSize": "13px", "color": "#444", "marginTop": "12px"},
            ),
        ], className="viz-box"),
    ], className="section rq-section"), id="section-rq1"),

    #-- RQ 2 -----------------------------------------------------------------
    html.Div(html.Section([
        html.H2([html.Span("RQ2", className="rq-section-number"), html.Span(" — How do MSCI World, Gold, and Bitcoin differ in direction and magnitude of abnormal returns following identical news spikes?", className="rq-section-title-text")]),
        html.P("The Graph shows the abnormal return in percent of the three Investments, on days with a high news count, meaning a signigicanty higher count than normal. The Percentages show how much the returns differ from the expected Trend (5 day) prediction"),

        #chart 1: abnormal returns
        html.Div([
            html.H3("Abnormal returns per Event"),
            html.Label("Days after event:"),
            #dropdown to select how many days after the event to calculate abnormal returns for (1, 3, 5, 7)
            dcc.Dropdown(
                options = DAYS_AFTER_OPTIONS,
                value = 3,
                id = "rq2-chart1-da",
                className ="dropdown",
                clearable = False
            ),
            #graph to show abnormal returns per event, with bars for each asset class (gold, bitcoin, msci world) and hover info showing z-score and significance
            dcc.Graph(id="rq2-graph-chart1"),
        ], className="viz-box"),

        #chart 2: event window
        html.Div([
            html.Div([
                html.H3("Event Window around single event"),
                html.Div([
                    html.Label("Event:"),
                    #dropdown to select which event to show (options are the shared spike days)
                    dcc.Dropdown(
                        options = EVENT_OPTIONS,
                        value = str(shared_spike_days[0]) if shared_spike_days else None,
                        id = "rq2-chart2-event",
                        className ="dropdown",
                        clearable = False
                    ),

                ], style = {"width": "35%"}),
                html.Div([
                    html.Label("Days before event:"),
                    #dropdown to select how many days before the event to show (3, 5, 7, 10)
                    dcc.Dropdown(
                        options = DAYS_BEFORE_OPTIONS,
                        value = 5,
                        id = "rq2-chart2-db",
                        className ="dropdown",
                        clearable = False
                    ),
                ], style = {"width": "25%"}),
                html.Div([
                    html.Label("Days after event:"),
                    #dropdown to select how many days after the event to show (1, 3, 5, 7)
                    dcc.Dropdown(
                        options = DAYS_AFTER_OPTIONS,
                        value = 5,
                        id = "rq2-chart2-da",
                        className ="dropdown",
                        clearable = False
                    ),
                ], style = {"width": "25%"}),
            ], style = {"display": "flex", "gap": "20px", "marginBottom": "10px"}),
            #graph to show price path for each asset class (gold, bitcoin, msci world) around the selected event, with x-axis as days relative to event and y-axis as normalized price (day -1 = 100%), and a vertical line at day 0 to indicate the event
            dcc.Graph(id="rq2-graph-chart2"),
        ],className = "viz-box"),

        html.Div([
            html.H3("Cumulative Abnormal Return - Day by Day Waterfall"),
            html.Div([
                html.Div([
                    html.Label("Event:"),
                    dcc.Dropdown(
                        options = EVENT_OPTIONS,
                        value = str(shared_spike_days[0]),
                        id ="rq2-chart3-event", className = "dropdown", clearable=False),
                ], style = {"width": "35%"}),
                html.Div([
                    html.Label("Days after event:"),
                    dcc.Dropdown(
                        options = DAYS_AFTER_OPTIONS,
                        value = 5,
                        id = "rq2-chart3-da", className="dropdown", clearable=False),
                ], style = {"width": "25%"}),
            ], style = {"display": "flex", "gap": "20px", "marginBottom": "10px"}),
            dcc.Graph(id = "rq2-graph-chart3"),
        ], className = "viz-box")
    ], className="section rq-section"), id="section-rq2", style=_HIDE),

    #-- RQ 3 -----------------------------------------------------------------------
    html.Div(html.Section([
        html.H2([html.Span("RQ3", className="rq-section-number"), html.Span(" — Does the average daily VADER sentiment score of Guardian articles predict the direction and magnitude of 3-day returns across assets?", className="rq-section-title-text")]),
        html.P("Uses VADER compound scores (−1 to +1) averaged per day per category. The violin chart shows the full return distribution per sentiment bucket; the bar chart compares mean returns across negative, neutral, and positive news days."),

        html.Div([
            html.Div([
                html.Label("Return window (days)"),
                dcc.Dropdown(
                    id="rq3-window",
                    options=[{"label": f"{d} days", "value": d} for d in [3, 5, 7, 14]],
                    value=3,
                    clearable=False,
                    className="dropdown",
                ),
            ], style={"width": "160px"}),
            html.Div([
                html.Label("Negative threshold (VADER ≤)"),
                dcc.Slider(
                    id="rq3-neg-threshold",
                    min=-0.3, max=-0.01, step=0.01, value=-0.05,
                    marks={v: str(v) for v in [-0.3, -0.2, -0.1, -0.05, -0.01]},
                ),
            ], style={"width": "360px"}),
            html.Div([
                html.Label("Positive threshold (VADER ≥)"),
                dcc.Slider(
                    id="rq3-pos-threshold",
                    min=0.01, max=0.3, step=0.01, value=0.05,
                    marks={v: str(v) for v in [0.01, 0.05, 0.1, 0.2, 0.3]},
                ),
            ], style={"width": "360px"}),
        ], style={"display": "flex", "gap": "30px", "alignItems": "flex-end", "marginBottom": "16px"}),

        html.Div([
            html.H3("Return Distribution by Sentiment"),
            dcc.Graph(id="rq3-heatmap"),
            html.P(
                "Takeaway: The return distributions for negative, neutral and positive sentiment days overlap almost entirely across all categories and assets, "
                "indicating that VADER sentiment scores do not meaningfully separate high- from low-return days. "
                "Gold is a consistent exception — its distribution sits above zero in all buckets, reflecting a persistent uptrend rather than a sentiment-driven effect. "
                "Widening the return window to 7–14 days does not reveal a clearer separation, confirming that sentiment in Guardian articles has negligible short-term predictive power for any of the three assets.",
                style={"backgroundColor": "#f0f4f8", "padding": "12px 16px", "borderLeft": "3px solid #4a9eda",
                       "fontSize": "13px", "color": "#444", "marginTop": "12px"},
            ),
        ], className="viz-box"),

        html.Div([
            html.H3("Average Return by Sentiment Bucket (± 1 SE)"),
            dcc.Graph(id="rq3-buckets"),
            html.P(
                "Takeaway: Error bars show that almost all bucket differences are well within ±1 SE of each other, confirming no reliable sentiment signal. "
                "The most notable exception is Bitcoin under Trade Policy: positive-sentiment days yield a mean return of −0.78% (n = 103), "
                "notably lower than negative-sentiment days (−0.12%, n = 249) — a potential 'buy the rumour, sell the news' pattern. "
                "Gold earns positive mean returns in every bucket and category (+0.5% to +1.0%), driven by its underlying bull trend rather than sentiment. "
                "MSCI World hovers near zero across all buckets with overlapping error bars, indicating no directional sentiment effect on equities.",
                style={"backgroundColor": "#f0f4f8", "padding": "12px 16px", "borderLeft": "3px solid #4a9eda",
                       "fontSize": "13px", "color": "#444", "marginTop": "12px"},
            ),
        ], className="viz-box"),
    ], className="section rq-section"), id="section-rq3", style=_HIDE),

    #---RQ4--------------------------------------------------------------------------
    html.Div(html.Section([
    html.H2([html.Span("RQ4", className="rq-section-number"), html.Span(" — Do simultaneous spikes across multiple news categories amplify 3-day returns compared to isolated single-category spikes?", className="rq-section-title-text")]),
    html.P("Comparing abnormal returns after single-category vs multi-category Trump news spikes."),
    #chart 1
    html.Div([
        html.H3("Single vs Multi-Category Spike Returns"),
        html.Label("Days after event:"),
        dcc.Dropdown(
            options= DAYS_AFTER_OPTIONS,
            value=5,
            id="rq4-da1", className="dropdown", clearable=False
        ),
        dcc.Graph(id="rq4-graph-chart1"),
    ], className="viz-box"),
    
    #chart 2
    html.Div([
        html.H3("Returns by news Category per asset"),
        html.Div([
            html.Div([
                html.Label("Asset:"),
                dcc.Dropdown(
                    options=[{"label": a, "value": a} for a in all_daily_returns.keys()],
                    value=list(all_daily_returns.keys())[0],
                    id="rq4-asset", className="dropdown", clearable=False
                ),
            ], style={"width": "35%"}),
            html.Div([
                html.Label("Days after event:"),
                dcc.Dropdown(
                    options=DAYS_AFTER_OPTIONS,
                    value=5,
                    id="rq4-da2", className="dropdown", clearable=False
                ),], style={"width": "25%"}),
            ], style={"display": "flex", "gap": "20px", "marginBottom": "10px"}),
            dcc.Graph(id="rq4-graph2"),   # ✅ inside the viz-box
        ], className="viz-box"),
    ], className="section rq-section"), id="section-rq4", style=_HIDE),

    # ── RQ 5 ──────────────────────────────────────────────────────────────────
    html.Div(html.Section([
        html.H2([html.Span("RQ5", className="rq-section-number"), html.Span(" — Above which daily article volume does a return exceeding 1% first consistently appear — and does this threshold differ by category?", className="rq-section-title-text")]),
        html.P(
            "Days are grouped into equal-frequency bins by article count. "
            "The top panel shows average forward returns per bin; the bottom panel "
            "shows how often returns exceed the movement threshold. "
            "The estimated threshold is the lower bound of the first bin where "
            ">50 % of days cross the threshold."
        ),

        # ── controls ──────────────────────────────────────────────────────────
        html.Div([
            html.Div([
                html.Label("News category"),
                dcc.Dropdown(
                    id="rq5-category",
                    options=[
                        {"label": "Trade Policy",      "value": "trade_policy"},
                        {"label": "Geopolitics",        "value": "geopolitics"},
                        {"label": "Domestic Politics",  "value": "domestic_politics"},
                    ],
                    value="trade_policy",
                    clearable=False,
                    className="dropdown",
                ),
            ], style={"width": "200px"}),
            html.Div([
                html.Label("Return window (days)"),
                dcc.Dropdown(
                    id="rq5-window",
                    options=[{"label": f"{d} days", "value": d} for d in [3, 5, 7]],
                    value=3,
                    clearable=False,
                    className="dropdown",
                ),
            ], style={"width": "150px"}),
            html.Div([
                html.Label("Movement threshold (%)"),
                dcc.Slider(
                    id="rq5-threshold",
                    min=0.5, max=3.0, step=0.5, value=1.0,
                    marks={v: f"{v}%" for v in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]},
                ),
            ], style={"width": "340px"}),
            html.Div([
                html.Label("Number of bins"),
                dcc.Slider(
                    id="rq5-bins",
                    min=3, max=8, step=1, value=5,
                    marks={v: str(v) for v in range(3, 9)},
                ),
            ], style={"width": "240px"}),
        ], style={"display": "flex", "gap": "30px", "alignItems": "flex-end", "marginBottom": "16px"}),

        html.Div([
            html.H3("Article volume vs. market reaction"),
            dcc.Graph(id="rq5-bins-chart"),
        ], className="viz-box"),

        html.Div([
            html.H3("Estimated threshold per news category"),
            dcc.Graph(id="rq5-summary-chart"),
        ], className="viz-box"),
    ], className="section rq-section"), id="section-rq5", style=_HIDE),

    # ── RQ 6 ──────────────────────────────────────────────────────────────────
    html.Div(html.Section([
        html.H2([html.Span("RQ6", className="rq-section-number"), html.Span(" — Within a 5-day post-spike window, how quickly does each asset reach its peak return — and does the lag differ across news categories?", className="rq-section-title-text")]),
        html.P(
            "For every spike day, the cumulative return is tracked over the following "
            "5 trading days. The line chart shows the average return profile per asset; "
            "the star marker indicates the day of peak absolute return. "
            "The heatmap gives a cross-category overview."
        ),

        # ── controls ──────────────────────────────────────────────────────────
        html.Div([
            html.Div([
                html.Label("Spike threshold (× std)"),
                dcc.Slider(
                    id="rq6-spike-mult",
                    min=0.5, max=2.5, step=0.25, value=1.0,
                    marks={v: str(v) for v in [0.5, 1.0, 1.5, 2.0, 2.5]},
                ),
            ], style={"width": "360px"}),
            html.Div([
                html.Label("Max lag window (days)"),
                dcc.Dropdown(
                    id="rq6-max-lag",
                    options=[{"label": f"{d} days", "value": d} for d in [3, 5, 7]],
                    value=5,
                    clearable=False,
                    className="dropdown",
                ),
            ], style={"width": "160px"}),
        ], style={"display": "flex", "gap": "30px", "alignItems": "flex-end", "marginBottom": "16px"}),

        html.Div([
            html.H3("Average cumulative return after spike (line per asset)"),
            dcc.Graph(id="rq6-lag-chart"),
        ], className="viz-box"),

        html.Div([
            html.H3("Peak lag heatmap — all categories × all assets"),
            html.P("Same spike threshold as above applies.", style={"color": "#888", "fontSize": "13px"}),
            dcc.Graph(id="rq6-heatmap"),
        ], className="viz-box"),
    ], className="section rq-section"), id="section-rq6", style=_HIDE),

    # ── RQ 7 ──────────────────────────────────────────────────────────────────
    html.Div(html.Section([
        html.H2([html.Span("RQ7", className="rq-section-number"), html.Span(" — Which category generates the most daily coverage — and does the volume ranking match the ranking by correlation strength with asset returns?", className="rq-section-title-text")]),
        html.P("Compares each category's share of total article volume (left) against its market correlation strength (right). A mismatch means niche but politically sensitive topics drive stronger market reactions than high-volume general coverage."),

        html.Div([
            html.H3("Volume vs Correlation Ranking"),
            html.P("Uses the same return window and normalisation selected in RQ1.", style={"color": "#888", "fontSize": "13px"}),
            dcc.Graph(id="rq7-overview"),
            html.P(
                "Takeaway: Domestic Politics dominates article volume (≈ 30 articles/day), followed by Geopolitics (≈ 26) and Trade Policy (≈ 18). "
                "The correlation ranking is almost exactly reversed: Trade Policy has by far the strongest market signal (mean |r| ≈ 0.41 in the 7-day/z-score configuration), "
                "while the two higher-volume categories have negligible correlations (|r| < 0.09). "
                "This inversion suggests that coverage volume alone does not predict market impact — "
                "trade policy decisions carry direct economic consequences that markets respond to, whereas general political coverage does not.",
                style={"backgroundColor": "#f0f4f8", "padding": "12px 16px", "borderLeft": "3px solid #4a9eda",
                       "fontSize": "13px", "color": "#444", "marginTop": "12px"},
            ),
        ], className="viz-box"),
    ], className="section rq-section"), id="section-rq7", style=_HIDE),

], className="page")


# ── RQ selector callbacks ─────────────────────────────────────────────────────
import urllib.parse

@callback(
    *[Output(f"section-{rq}", "style") for rq in RQS],
    Input("rq-selector", "value"),
)
def show_section(selected):
    return [_SHOW if rq == selected else _HIDE for rq in RQS]


@callback(
    Output("rq-selector", "value"),
    Input("_pages_location", "search"),
    *[Input(f"rq-btn-{rq}", "n_clicks") for rq in RQS],
)
def set_rq(search, *_btn_clicks):
    triggered = ctx.triggered_id
    if triggered == "_pages_location":
        if search:
            params = urllib.parse.parse_qs(search.lstrip("?"))
            rq = params.get("rq", [None])[0]
            if rq in RQS:
                return rq
        return dash.no_update
    if isinstance(triggered, str) and triggered.startswith("rq-btn-"):
        return triggered.replace("rq-btn-", "")
    return dash.no_update


@callback(
    *[Output(f"rq-btn-{rq}", "className") for rq in RQS],
    Input("rq-selector", "value"),
)
def update_btn_classes(selected):
    return ["rq-btn rq-btn-active" if rq == selected else "rq-btn" for rq in RQS]


# ── RQ1 / RQ7 callbacks ──────────────────────────────────────────────────────

def _build_master(n_days, threshold, normalize):
    returns = compute_3d_returns(_market, n_days=n_days)
    master  = build_master_dynamic(_counts, _market, returns, _sentiment, threshold=threshold)
    if normalize == "zscore":
        zscores = compute_normalized_counts(_counts)
        for cat in ["trade_policy", "geopolitics", "domestic_politics"]:
            master[f"{cat}_count"] = zscores[f"{cat}_zscore"]
    return master

@callback(
    Output("rq1-heatmap", "figure"),
    Output("rq1-scatter",  "figure"),
    Output("rq7-overview", "figure"),
    Input("rq1-window",    "value"),
    Input("rq1-threshold", "value"),
    Input("rq1-normalize", "value"),
)
def update_rq1_rq7(n_days, threshold, normalize):
    label  = f"{n_days}-day return | {'z-score' if normalize == 'zscore' else 'raw count'} | threshold={threshold}"
    master = _build_master(n_days, threshold, normalize)
    return (
        fig_rq1_heatmap(master,  config_label=label),
        fig_rq1_scatter(master,  config_label=label),
        fig_rq7_overview(master),
    )


# ── RQ3 callbacks ─────────────────────────────────────────────────────────────

@callback(
    Output("rq3-heatmap", "figure"),
    Output("rq3-buckets", "figure"),
    Input("rq3-window",        "value"),
    Input("rq3-neg-threshold", "value"),
    Input("rq3-pos-threshold", "value"),
)
def update_rq3(n_days, neg_threshold, pos_threshold):
    returns = compute_3d_returns(_market, n_days=n_days)
    master  = build_master_dynamic(_counts, _market, returns, _sentiment)
    return (
        fig_rq3_violin(master, negative_threshold=neg_threshold, positive_threshold=pos_threshold),
        fig_rq3_buckets(master, negative_threshold=neg_threshold, positive_threshold=pos_threshold),
    )


# ── RQ2 callbacks ─────────────────────────────────────────────────────────────
@callback(
    Output("rq2-graph-chart1", "figure"),
    Input("rq2-chart1-da", "value")
)
def update_rq2_chart1(days_after):
    return build_chart1(days_after)

@callback(
    Output("rq2-graph-chart2", "figure"),
    Input("rq2-chart2-event", "value"),
    Input("rq2-chart2-db",    "value"),
    Input("rq2-chart2-da",    "value")
)
def update_rq2_chart2(event, days_before, days_after):
    return build_chart2(event, days_before, days_after)

@callback(
        Output("rq2-graph-chart3", "figure"),
        Input("rq2-chart3-event", "value"),
        Input("rq2-chart3-da", "value")
)
def update_rq2_chart3(event, days_after):
    return build_chart3(event, days_after)
# ── RQ4 callbacks ─────────────────────────────────────────────────────────────
@callback(
    Output("rq4-graph-chart1", "figure"),
    Input("rq4-da1", "value")
)
def update_rq4_chart1(days_after):
    return build_chart_rq4(days_after)

@callback(
    Output("rq4-graph2", "figure"),
    Input("rq4-asset", "value"),
    Input("rq4-da2",   "value")
)
def update_rq4_chart2(asset, days_after):
    return build_chart_rq4_category_breakdown(asset, days_after)


# ── RQ5 callbacks ─────────────────────────────────────────────────────────────
@callback(
    Output("rq5-bins-chart",    "figure"),
    Output("rq5-summary-chart", "figure"),
    Input("rq5-category",  "value"),
    Input("rq5-window",    "value"),
    Input("rq5-threshold", "value"),
    Input("rq5-bins",      "value"),
)
def update_rq5(category, return_window, movement_threshold, n_bins):
    if not _rq56_available:
        return go.Figure(), go.Figure()
    return (
        fig_rq5_bins(_df_rq5, category=category, return_window=return_window,
                     movement_threshold=movement_threshold, n_bins=n_bins),
        fig_rq5_threshold_summary(_df_rq5, return_window=return_window,
                                  movement_threshold=movement_threshold, n_bins=n_bins),
    )


# ── RQ6 callbacks ─────────────────────────────────────────────────────────────
@callback(
    Output("rq6-lag-chart", "figure"),
    Output("rq6-heatmap",   "figure"),
    Input("rq6-spike-mult", "value"),
    Input("rq6-max-lag",    "value"),
)
def update_rq6(spike_multiplier, max_lag):
    if not _rq56_available:
        return go.Figure(), go.Figure()
    return (
        fig_rq6_lag_profiles(_df_rq6, spike_multiplier=spike_multiplier, max_lag=max_lag),
        fig_rq6_peak_heatmap(_df_rq6, spike_multiplier=spike_multiplier, max_lag=max_lag),
    )