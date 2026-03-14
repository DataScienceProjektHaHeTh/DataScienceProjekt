from dash import Dash, html, dcc
import dash

app = Dash(__name__, use_pages=True, suppress_callback_exceptions=True)
server = app.server  # expose Flask server for gunicorn

#define the app layout, like the top navbar)
app.layout = html.Div([
    # Navigation Bar
    html.Nav([
        dcc.Link("Home",            href="/",                className="nav-link"),
        html.Div([
            dcc.Link("Analysis & Results", href="/visualizations", className="nav-link"),
            html.Div([
                dcc.Link("RQ1 — News Frequency vs Returns",  href="/visualizations?rq=rq1", className="nav-dropdown-item"),
                dcc.Link("RQ2 — Asset Response to Spikes",  href="/visualizations?rq=rq2", className="nav-dropdown-item"),
                dcc.Link("RQ3 — Sentiment vs Returns",      href="/visualizations?rq=rq3", className="nav-dropdown-item"),
                dcc.Link("RQ4 — Multi-Category Spikes",     href="/visualizations?rq=rq4", className="nav-dropdown-item"),
                dcc.Link("RQ5 — Article Volume Threshold",  href="/visualizations?rq=rq5", className="nav-dropdown-item"),
                dcc.Link("RQ6 — Asset Reaction Speed",      href="/visualizations?rq=rq6", className="nav-dropdown-item"),
                dcc.Link("RQ7 — Volume vs Correlation",     href="/visualizations?rq=rq7", className="nav-dropdown-item"),
            ], className="nav-dropdown-menu"),
        ], className="nav-dropdown"),
        dcc.Link("Approach & Assumptions", href="/about-project", className="nav-link"),
        dcc.Link("Meet the Team",            href="/about-team",      className="nav-link"),
    ], className="navbar"),

    # Page content
    html.Main([
        dash.page_container
    ], className="main-content"),

    # Footer
    html.Footer([
        html.Div([

            html.Div([
                html.H4("Impressum", className="footer-heading"),
                html.P("Hansen, Jan Ole", className="footer-text"),
                html.P("Hempel, Fridjoff", className="footer-text"),
                html.P("Thielert, Nico", className="footer-text"),
                html.P("Christian-Albrechts-Universität zu Kiel", className="footer-text"),
                html.P("Data Science Project · WiSe 2025/26 · Group 11", className="footer-text"),
                html.P(
                    "This website was produced for academic purposes only and does not "
                    "constitute financial advice.",
                    className="footer-disclaimer"
                ),
            ], className="footer-col"),

            html.Div(className="footer-separator"),

            html.Div([
                html.H4("Data Sources", className="footer-heading"),
                html.P("News: The Guardian Open Platform API", className="footer-text"),
                html.P("Market data: Yahoo Finance (yfinance)", className="footer-text"),
                html.P("Assets: MSCI World (URTH), Gold (GC=F), Bitcoin (BTC-USD)", className="footer-text"),
                html.P("Period: January 2025 – present", className="footer-text"),
                html.P("Sentiment: VADER (NLTK)", className="footer-text"),
            ], className="footer-col"),

            html.Div(className="footer-separator"),

            html.Div([
                html.H4("Navigation", className="footer-heading"),
                dcc.Link("Home",               href="/",                className="footer-link"),
                dcc.Link("Analysis & Results", href="/visualizations",  className="footer-link"),
                dcc.Link("Approach & Assumptions", href="/about-project", className="footer-link"),
                dcc.Link("Team",               href="/about-team",      className="footer-link"),
            ], className="footer-col"),

        ], className="footer-inner"),

        html.Div(
            "© 2025 · CAU Kiel · Data Science Project · Group 11",
            className="footer-bottom"
        ),
    ], className="site-footer"),
])

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)