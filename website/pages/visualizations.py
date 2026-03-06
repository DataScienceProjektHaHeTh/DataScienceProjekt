import dash
from dash import html, dcc, callback, Output, Input
import plotly.graph_objects as go

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
PLACEHOLDER_OPTIONS = [
    {"label": "Option A", "value": "a"},
    {"label": "Option B", "value": "b"},
    {"label": "Option C", "value": "c"},
]

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

        html.Div([
            html.H3("Interactive Chart"),
            dcc.Dropdown(PLACEHOLDER_OPTIONS, "a", id="rq2-dropdown", className="dropdown"),
            dcc.Graph(id="rq2-graph"),
        ], className="viz-box"),

        html.Div([
            html.H3("Static Chart"),
            dcc.Graph(figure=placeholder_fig("Static chart for RQ2 — replace with your figure")),
        ], className="viz-box"),
    ], className="section rq-section"),

], className="page")

# ── Callbacks (swap placeholder_fig() with real figures later) ─────────────────
@callback(Output("rq1-graph", "figure"), Input("rq1-dropdown", "value"))
def update_rq1(value):
    # TODO: replace with real data & chart
    return placeholder_fig(f"RQ1 interactive chart — selected: {value}")

@callback(Output("rq2-graph", "figure"), Input("rq2-dropdown", "value"))
def update_rq2(value):
    return placeholder_fig(f"RQ2 interactive chart — selected: {value}")

@callback(Output("rq3-graph", "figure"), Input("rq3-dropdown", "value"))
def update_rq3(value):
    return placeholder_fig(f"RQ3 interactive chart — selected: {value}")