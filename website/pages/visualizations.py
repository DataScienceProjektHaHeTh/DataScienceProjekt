import dash
import sys
import os
from dash import html, dcc, callback, Output, Input
import plotly.graph_objects as go

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.research_question_implementations.research_question_2_implementation import (
    calculate_price_return, load_price_data,
    shared_spike_days, all_daily_closes,
    build_chart1, build_chart2
)
from src.research_question_implementations.research_question_4_implementation import (
    build_chart_rq4,
    build_chart_rq4_category_breakdown,
    all_daily_returns
)

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

# ── Placeholder dropdown options ───────────────────────────────────────────────
PLACEHOLDER_OPTIONS = [{"label": "Option A", "value": "a"},
    {"label": "Option B", "value": "b"},
    {"label": "Option C", "value": "c"},
]

# For RQ2 dropdowns
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
        html.H2("RQ1: Placeholder Research Question 1"),
        html.P("Placeholder: Describe what this visualization shows and what insight it reveals."),

        html.Div([
            html.H3("Interactive Chart"),
            dcc.Dropdown(PLACEHOLDER_OPTIONS, "a", id="rq1-dropdown", className="dropdown"),
            dcc.Graph(id="rq1-graph"),
        ], className="viz-box"),

        html.Div([
            html.H3("Static Chart"),
            dcc.Graph(figure=placeholder_fig("Static chart for RQ1 — replace with your figure")),
        ], className="viz-box"),
    ], className="section rq-section"),

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
], className = "page")


#-- Callbacks ------------------------------------------

#-- RQ2 ----------------------------------------------
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


#-- RQ4 ---------------------------------------------------------
@callback(
    Output("rq4-graph-chart1", "figure"),
    Input("rq4-da", "value")
)
def update_rq4(days_after):
    return build_chart_rq4(days_after)

@callback(
    Output("rq4-graph2", "figure"),
    Input("rq4-asset", "value"),
    Input("rq4-da2",   "value")
)
def update_rq4_breakdown(asset, days_after):
    return build_chart_rq4_category_breakdown(asset, days_after)