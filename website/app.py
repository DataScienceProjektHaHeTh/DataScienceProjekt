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
        dcc.Link("About Project",   href="/about-project",   className="nav-link"),
        dcc.Link("Team",            href="/about-team",      className="nav-link"),
    ], className="navbar"),

    # Page content
    html.Main([
        dash.page_container
    ], className="main-content")
])

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)