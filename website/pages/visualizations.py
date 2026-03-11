import dash
import sys
import os
from dash import html, dcc, callback, Output, Input
import plotly.graph_objects as go

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

try:
    from src.analysis_rq1_rq3_rq7.rq2_spikedays import (
        calculate_price_return, load_price_data,
        shared_spike_days, all_daily_closes,
        build_chart1, build_chart2
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
    fig_rq3_heatmap, fig_rq3_buckets,
)

# Load base data once at startup — callbacks reuse this without re-reading files
_counts, _market, _returns_default, _sentiment = load_base_data()

dash.register_page(__name__, path="/visualizations", name="Visualizations")

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

# ── RQ2 dropdown options ───────────────────────────────────────────────────────
EVENT_OPTIONS   = [{"label": str(e), "value": str(e)} for e in shared_spike_days]
DAYS_AFTER_OPTIONS      = [{"label": f"{d} days after",  "value": d} for d in [1, 3, 5, 7]]
DAYS_BEFORE_OPTIONS      = [{"label": f"{d} days before", "value": d} for d in [3, 5, 7, 10]]


# ── Layout ─────────────────────────────────────────────────────────────────────
layout = html.Div([
    html.H1("Visualizations"),
    html.P(
        "All interactive and static visualizations for each research question.",
        className="page-subtitle"
    ),

    # ── RQ 1 ──────────────────────────────────────────────────────────────────
    html.Section([
        html.H2("RQ1: Does article volume in a news category correlate with market returns?"),
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
        ], className="viz-box"),

        html.Div([
            html.H3("Scatter Grid — Spike Days"),
            html.P("Same parameters as above apply.", style={"color": "#888", "fontSize": "13px"}),
            dcc.Graph(id="rq1-scatter"),
        ], className="viz-box"),
    ], className="section rq-section"),

    # ── RQ 7 ──────────────────────────────────────────────────────────────────
    html.Section([
        html.H2("RQ7: Does higher coverage volume mean stronger market correlation?"),
        html.P("Compares each category's average daily article volume (left) against its market correlation strength (right). A mismatch means niche but politically sensitive topics drive stronger market reactions than high-volume general coverage."),

        html.Div([
            html.H3("Volume vs Correlation Ranking"),
            html.P("Uses the same return window and normalisation selected in RQ1.", style={"color": "#888", "fontSize": "13px"}),
            dcc.Graph(id="rq7-overview"),
        ], className="viz-box"),
    ], className="section rq-section"),

    # ── RQ 3 ──────────────────────────────────────────────────────────────────
    html.Section([
        html.H2("RQ3: Does the sentiment of news articles correlate with market returns?"),
        html.P("Uses VADER compound scores (−1 to +1) averaged per day per category. The heatmap shows direct correlation; the bucket chart compares mean returns across negative, neutral, and positive news days."),

        html.Div([
            html.H3("Sentiment Correlation Heatmap"),
            dcc.Graph(id="rq3-heatmap"),
        ], className="viz-box"),

        html.Div([
            html.H3("Average Return by Sentiment Bucket"),
            html.Div([
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
            ], style={"display": "flex", "gap": "40px", "marginBottom": "16px"}),
            dcc.Graph(id="rq3-buckets"),
        ], className="viz-box"),
    ], className="section rq-section"),

    # ── RQ 2 — edit here ──────────────────────────────────────────────────────
    # ── RQ 2 ──────────────────────────────────────────────────────────────────
    html.Section([
        html.H2("RQ2: Placeholder Research Question 2"),
        html.P("Placeholder: Describe what this visualization shows and what insight it reveals."),

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
                        value = str(shared_spike_days[0]),
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
    ], className="section rq-section"),


    #---RQ4--------------------------------------------------------------------------
    html.Section([
    html.H2("RQ4: Do multi-category news spikes amplify market returns?"),
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
            html.Label("Asset:"),
            dcc.Dropdown(
                options = EVENT_OPTIONS,
                value = 3,
                id = "rq4-asset", className = "dropdown", clearable = False
            ),
        ], style={"width": "35%"}),
        html.Div([
            html.Label("Days after event:"),
            dcc.Dropdown(
                options = DAYS_AFTER_OPTIONS,
                value = 5,
                id = "rq4-da2", className = "dropdown", clearable = False
            ),
        ], style = {"width": "25%"})
    ], style = {"display": "flex", "gap": "20px", "marginBottom": "10px"}),
    dcc.Graph(id = "rq4-graph2")
    ], className="section rq-section"),

    # ── RQ 5 — edit here ──────────────────────────────────────────────────────
    html.Section([
        html.H2("RQ5: Placeholder Research Question 5"),
        html.P("Visualizations coming soon — replace this section with your charts."),
        html.Div([
            html.H3("Chart placeholder"),
            dcc.Graph(figure=placeholder_fig("RQ5 chart — add your figure here")),
        ], className="viz-box"),
    ], className="section rq-section"),

    # ── RQ 6 — edit here ──────────────────────────────────────────────────────
    html.Section([
        html.H2("RQ6: Placeholder Research Question 6"),
        html.P("Visualizations coming soon — replace this section with your charts."),
        html.Div([
            html.H3("Chart placeholder"),
            dcc.Graph(figure=placeholder_fig("RQ6 chart — add your figure here")),
        ], className="viz-box"),
    ], className="section rq-section"),

], className = "page")


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
    Output("rq3-heatmap",  "figure"),
    Output("rq3-buckets",  "figure"),
    Input("rq3-neg-threshold", "value"),
    Input("rq3-pos-threshold", "value"),
)
def update_rq3(neg_threshold, pos_threshold):
    master = build_master_dynamic(_counts, _market, _returns_default, _sentiment)
    return (
        fig_rq3_heatmap(master),
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