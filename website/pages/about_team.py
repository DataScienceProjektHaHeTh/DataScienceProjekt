import dash
from dash import html

dash.register_page(__name__, path="/about-team", name="Team")

#function to create team member cards
def team_card(name, bio, emoji="👤"):
    return html.Div([
        html.Div(emoji, className="team-avatar"),
        html.H3(name, className="team-name"),
        html.P(bio, className="team-bio"),
    ], className="team-card")

layout = html.Div([
    html.H1("Meet the Team"),
    html.P("The people behind this project.", className="page-subtitle"),

    #Insert Pictures?
    html.Div([
        team_card(
            name="Hansen, Jan Ole",
            bio="Jan Ole led the event-study work for RQ2 and RQ4, designing the abnormal-return methodology and building the spike-day comparison charts. He is studying computer science at CAU Kiel and has a particular interest in empirical finance and time-series analysis. For this project he was responsible for the market data pipeline, the sentiment analysis of the guardian articles, as well as taking care of the kanban board used for organization in the group  and the RQ2/RQ4 visualizations on the website.",
            emoji="👤"
        ),
        team_card(
            name="Hempel, Fridjoff",
            bio="Fridjoff built the core data infrastructure — the shared data loader, the processed CSV pipeline, and the Dash web application — and led the analysis for RQ5 and RQ6. He is studying computer science at CAU Kiel with a focus on data engineering and software development. His rolling z-score normalisation idea proved to be the single most impactful methodological improvement, unlocking the statistically significant flight-to-safety pattern in the data.",
            emoji="👤"
        ),
        team_card(
            name="Thielert, Nico",
            bio="Nico was responsible for the correlation analysis underlying RQ1 and RQ7 as well as the VADER sentiment pipeline for RQ3. He is studying computer science at CAU Kiel and is interested in the intersection of political events and quantitative finance. His systematic parameter sweep — testing five return windows, four lag offsets, and two normalisation methods — revealed that the weak default correlations were an artefact of the 3-day window assumption rather than a true absence of market signal.",
            emoji="👤"
        ),
    ], className="team-grid"),

], className="page")