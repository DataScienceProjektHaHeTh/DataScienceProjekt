import dash
from dash import html, dcc

dash.register_page(__name__, path="/", name="Home")

layout = html.Div([

    # ── Newspaper-style header ─────────────────────────────────────────────────
    html.Header([

        # Edition / kicker line
        html.Div([
            html.Span("Data Science Project · WiSe 2025/26 · CAU Kiel · Group 11",
                      className="newspaper-kicker"),
        ], className="newspaper-kicker-row"),

        # Main headline
        html.H1([
            html.Span("Trump,", className="headline-trump"),
            html.Span(" Tariffs & Trade-Turbulence", className="headline-main"),
        ], className="newspaper-headline"),

        html.P(
            "How Trump-related political news moves financial markets — "
            "a data-driven analysis of MSCI World, Gold and Bitcoin.",
            className="newspaper-subheadline"
        ),

        html.Hr(className="newspaper-rule"),

        # Two-column body: summary left, photo right
        html.Div([
            html.Div([
                html.P(
                    "This project examines whether Trump-related news coverage in The Guardian predicts "
                    "short-term price movements in MSCI World, Gold, and Bitcoin during his second term. "
                    "We collected daily article counts and VADER sentiment scores across three news "
                    "categories — Trade Policy, Geopolitics, and Domestic Politics — and matched them "
                    "against forward returns over 3–14 day windows.",
                    className="newspaper-body-text"
                ),
                html.P(
                    "Using Spearman correlation, event-study methods, and threshold analysis across "
                    "seven research questions, we find that Trade Policy coverage produces a measurable "
                    "flight-to-safety effect, while sentiment scores and general political coverage show "
                    "no predictive power. Our results suggest it is the economic specificity of a news "
                    "category, not its volume or tone, that determines market impact.",
                    className="newspaper-body-text"
                ),
            ], className="newspaper-col-text"),

            html.Div([
                html.Img(src="/assets/donald-trump-home.png", className="trump-image"),
            ], className="newspaper-col-image"),
        ], className="newspaper-columns"),

    ], className="newspaper-header"),

    # ── Key Findings ──────────────────────────────────────────────────────────
    html.Section([
        html.H2("Key Findings", className="newspaper-section-title"),
        html.Div([

            dcc.Link(html.Div([
                html.H3("Trade Policy Triggers Flight to Safety"),
                html.P(
                    "Spikes in Trade Policy coverage correlate strongly with falling equities "
                    "(MSCI World r = −0.45) and crypto (Bitcoin r = −0.38) while Gold rises "
                    "(r = +0.40). No such signal exists for Geopolitics or Domestic Politics."
                ),
                html.Span("→ RQ1 & RQ7", className="card-rq-link"),
            ], className="card card-clickable newspaper-card"), href="/visualizations?rq=rq1"),

            dcc.Link(html.Div([
                html.H3("Sentiment Does Not Predict Returns"),
                html.P(
                    "VADER sentiment scores averaged across daily articles show near-zero correlations "
                    "with 3–14 day returns across all categories and assets. The news tone in "
                    "The Guardian carries no measurable short-term market signal."
                ),
                html.Span("→ RQ3", className="card-rq-link"),
            ], className="card card-clickable newspaper-card"), href="/visualizations?rq=rq3"),

            dcc.Link(html.Div([
                html.H3("Volume Does Not Equal Impact"),
                html.P(
                    "Domestic Politics generates the most coverage (≈30 articles/day) yet has the "
                    "weakest market signal. Trade Policy — with the lowest volume (≈18/day) — drives "
                    "the strongest correlations. Content specificity beats quantity."
                ),
                html.Span("→ RQ7", className="card-rq-link"),
            ], className="card card-clickable newspaper-card"), href="/visualizations?rq=rq7"),

        ], className="card-grid"),
    ], className="section"),

], className="page")
