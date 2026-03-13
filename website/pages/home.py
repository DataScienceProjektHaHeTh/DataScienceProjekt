import dash
from dash import html

#setup the site for navigation
dash.register_page(__name__, path="/", name="Home")

layout = html.Div([

    # Main Section / Hero
    html.Section([
        html.H1("Trump, Tariffs and Turbulence: How Political News move the Financial Markets", className="hero-title", style = {"color": "#ffffff"}),
        html.P(
            "A data-driven analyses of how Trump-related Guardian news coverage correlates with the price of MSCI World, Gold and Bitcoin - looking at the second Trump term to the 'current' day.",
            className="hero-subtitle"
        ),
        #Info Charts
        html.Div([
            html.Span("WiSe 2025/26", className="badge"),
            html.Span("CAU Kiel", className="badge"),
            html.Span("Group 11", className="badge"),
        ], className="hero-badges")
    ], className="hero"),

    # Key Findings
    html.Section([
        html.H2("Key Findings"),
        #card items
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