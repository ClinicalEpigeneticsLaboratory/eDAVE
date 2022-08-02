import json
import dash
import dash_bootstrap_components as dbc

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], use_pages=True)
pages = [
    dbc.ListGroupItem(page["name"], href=page["path"])
    for page in dash.page_registry.values()
    if page["module"] != "pages.not_found_404"
]

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Home", href="/")),
        dbc.DropdownMenu(
            children=[dbc.DropdownMenuItem("Pages:", header=True), *pages],
            nav=True,
            in_navbar=True,
            label="More",
        ),
    ],
    brand="eDAVE v. 0.0.0.0",
    brand_href="/",
    color="primary",
    dark=True,
)

app.layout = dbc.Container([navbar, dash.page_container], fluid=True)
config = json.load(open("../config.json", "r"))

if __name__ == "__main__":
    app.run_server(debug=config["debug"])
