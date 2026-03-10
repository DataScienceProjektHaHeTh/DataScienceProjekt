from dash import Dash, html, dcc
import dash

app = Dash(__name__, use_pages=True, suppress_callback_exceptions=True)

#define the app layout, like the top navbar)
app.layout = html.Div([
    # Navigation Bar
    html.Nav([
        html.Div([
            html.Span("DS Project", className="nav-logo"),
            #Link Items in the Navbar, 
            html.Div([
                dcc.Link("Home",            href="/",                className="nav-link"),
                dcc.Link("About Project",   href="/about-project",   className="nav-link"),
                dcc.Link("Team",            href="/about-team",      className="nav-link"),
                dcc.Link("Visualizations",  href="/visualizations",  className="nav-link"),
            ], className="nav-links")
        ], className="nav-inner")
    ], className="navbar"),

    # Page content
    html.Main([
        dash.page_container
    ], className="main-content")
])

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=False)