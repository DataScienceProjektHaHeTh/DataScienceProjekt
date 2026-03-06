import dash
from dash import html

dash.register_page(__name__, path="/", name="Home")

layout = html.Div([

    # Hero Section
    html.Section([
        html.H1("Project Title", className="hero-title"),
        html.P(
            "Analyzing the effects of Trump related news on movements in the Stock Market.",
            className="hero-subtitle"
        ),
        html.Div([
            html.Span("WiSe 2025/26", className="badge"),
            html.Span("CAU Kiel", className="badge"),
            html.Span("Team Name", className="badge"),
        ], className="hero-badges")
    ], className="hero"),

    # Key Findings
    html.Section([
        html.H2("Key Findings"),
        html.Div([
            html.Div([
                html.Div("🔍", className="card-icon"),
                html.H3("Finding 1"),
                html.P("Placeholder: brief descriptions of our findings.")
            ], className="card"),
            html.Div([
                html.Div("📈", className="card-icon"),
                html.H3("Finding 2"),
                html.P("Placeholder: brief descriptions of our findings.")
            ], className="card"),
            html.Div([
                html.Div("💡", className="card-icon"),
                html.H3("Finding 3"),
                html.P("Placeholder: brief descriptions of our findings.")
            ], className="card"),
        ], className="card-grid")
    ], className="section"),

    # Project Summary
    html.Section([
        html.H2("Project Summary"),
        html.P(
            "Placeholder: Short summary of the project.",
            className="summary-text"
        ),
    ], className="section"),

], className="page")