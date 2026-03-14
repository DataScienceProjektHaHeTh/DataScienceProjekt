import dash
from dash import html, dcc

dash.register_page(__name__, path="/", name="Home")

layout = html.Div([

    html.Div([

        # ── Left column: hero then research questions ──────────────────────────
        html.Div([

            html.Header([
                html.Div([
                    html.Span("Data Science Project · WiSe 2025/26 · CAU Kiel · Group 11",
                              className="newspaper-kicker"),
                ], className="newspaper-kicker-row"),

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

                html.Div([
                    html.Div([
                        html.P(
                            "This project examines whether Trump-related news coverage in The Guardian "
                            "predicts short-term price movements in MSCI World, Gold, and Bitcoin during "
                            "his second term. We collected daily article counts and VADER sentiment scores "
                            "across three news categories — Trade Policy, Geopolitics, and Domestic Politics "
                            "— and matched them against forward returns over 3–14 day windows.",
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

            ], className="home-block"),

            html.Div([
                html.H2("Research Questions", className="newspaper-section-title"),
                html.Div([

                    dcc.Link(html.Div([
                        html.Span("RQ1", className="rq-number"),
                        html.Span("Does daily news frequency — split by topic — correlate with 3-day returns in MSCI World, Gold, and Bitcoin following a coverage spike?", className="rq-label"),
                    ], className="rq-link-item"), href="/visualizations?rq=rq1"),

                    dcc.Link(html.Div([
                        html.Span("RQ2", className="rq-number"),
                        html.Span("How do the three assets differ in direction and magnitude of 3-day abnormal returns following identical news spikes across all categories?", className="rq-label"),
                    ], className="rq-link-item"), href="/visualizations?rq=rq2"),

                    dcc.Link(html.Div([
                        html.Span("RQ3", className="rq-number"),
                        html.Span("Does the average daily VADER sentiment score of Guardian articles predict the direction and magnitude of 3-day returns across assets?", className="rq-label"),
                    ], className="rq-link-item"), href="/visualizations?rq=rq3"),

                    dcc.Link(html.Div([
                        html.Span("RQ4", className="rq-number"),
                        html.Span("Do simultaneous spikes across multiple news categories amplify 3-day returns compared to isolated single-category spikes?", className="rq-label"),
                    ], className="rq-link-item"), href="/visualizations?rq=rq4"),

                    dcc.Link(html.Div([
                        html.Span("RQ5", className="rq-number"),
                        html.Span("Above which daily article volume does a return exceeding 1% first consistently appear — and does this threshold differ by news category?", className="rq-label"),
                    ], className="rq-link-item"), href="/visualizations?rq=rq5"),

                    dcc.Link(html.Div([
                        html.Span("RQ6", className="rq-number"),
                        html.Span("Within a 5-day post-spike window, how quickly does each asset reach its peak return — and does the lag differ across the three news categories?", className="rq-label"),
                    ], className="rq-link-item"), href="/visualizations?rq=rq6"),

                    dcc.Link(html.Div([
                        html.Span("RQ7", className="rq-number"),
                        html.Span("Which category generates the most daily coverage — and does the volume ranking match the ranking by correlation strength with asset returns?", className="rq-label"),
                    ], className="rq-link-item"), href="/visualizations?rq=rq7"),

                ], className="rq-link-list"),
            ], className="home-block"),

        ], className="home-col-left"),

        # ── Right column: key findings then motivation ─────────────────────────
        html.Div([

            html.Section([
                html.H2("Key Findings", className="newspaper-section-title"),
                html.Div([

                    html.A(html.Div([
                        html.H3("Trade Policy Triggers Flight to Safety"),
                        html.P(
                            "Spikes in Trade Policy coverage correlate strongly with falling equities "
                            "(MSCI World r = −0.45) and crypto (Bitcoin r = −0.38) while Gold rises "
                            "(r = +0.40). No such signal exists for Geopolitics or Domestic Politics."
                        ),
                        html.Span("→ RQ1 & RQ7", className="card-rq-link"),
                    ], className="card card-clickable newspaper-card"), href="/visualizations?rq=rq1", className="card-link-wrapper"),

                    html.A(html.Div([
                        html.H3("Sentiment Does Not Predict Returns"),
                        html.P(
                            "VADER sentiment scores averaged across daily articles show near-zero "
                            "correlations with 3–14 day returns across all categories and assets. "
                            "The news tone in The Guardian carries no measurable short-term market signal."
                        ),
                        html.Span("→ RQ3", className="card-rq-link"),
                    ], className="card card-clickable newspaper-card"), href="/visualizations?rq=rq3", className="card-link-wrapper"),

                    html.A(html.Div([
                        html.H3("Volume Does Not Equal Impact"),
                        html.P(
                            "Domestic Politics generates the most coverage (≈30 articles/day) yet has the "
                            "weakest market signal. Trade Policy — with the lowest volume (≈18/day) — drives "
                            "the strongest correlations. Content specificity beats quantity."
                        ),
                        html.Span("→ RQ7", className="card-rq-link"),
                    ], className="card card-clickable newspaper-card"), href="/visualizations?rq=rq7", className="card-link-wrapper"),

                ], className="findings-col"),
            ], className="home-block"),

            html.Div([
                html.H2("Motivation", className="newspaper-section-title"),
                html.P(
                    "Donald Trump's second presidency has been marked by an unusually high pace of "
                    "politically consequential decisions: sweeping tariff announcements, shifts in NATO "
                    "commitments, executive orders targeting federal agencies, and ongoing geopolitical "
                    "crises. Each of these events generates a wave of media coverage and often a visible "
                    "reaction in financial markets.",
                    className="newspaper-body-text"
                ),
                html.P(
                    "But the relationship between political news and asset prices is rarely "
                    "straightforward. Does more coverage move markets, or does it just create noise? "
                    "Does negative news reliably send prices down? Do different asset classes react "
                    "differently? We chose this topic because it sits at the intersection of three "
                    "defining trends: an unusually media-intensive presidency, record levels of retail "
                    "market participation, and the growing role of alternative assets like Bitcoin.",
                    className="newspaper-body-text"
                ),
            ], className="home-block"),

        ], className="home-col-right"),

    ], className="home-columns"),

], className="page")
