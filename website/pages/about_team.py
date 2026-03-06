import dash
from dash import html

dash.register_page(__name__, path="/about-team", name="Team")

def team_card(name, role, bio, emoji="👤"):
    return html.Div([
        html.Div(emoji, className="team-avatar"),
        html.H3(name, className="team-name"),
        html.Span(role, className="team-role"),
        html.P(bio, className="team-bio"),
    ], className="team-card")

layout = html.Div([
    html.H1("Meet the Team"),
    html.P("The people behind this project.", className="page-subtitle"),

    html.Div([
        team_card(
            name="Hansen, Jan Ole",
            role="...",
            bio="Placeholder: Short bio — background, what was worked on in this project.",
            emoji="👤"
        ),
        team_card(
            name="Hempel, Fridjoff",
            role="...",
            bio="Placeholder: Short bio — background, what was worked on in this project.",
            emoji="👤"
        ),
        team_card(
            name="Thilert, Nico",
            role="...",
            bio="Placeholder: Short bio — background, what was worked on in this project.",
            emoji="👤"
        ),
    ], className="team-grid"),

], className="page")