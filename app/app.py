import json

import dash
import dash_bootstrap_components as dbc

with open("config.json", "r", encoding="UTF-8") as config_file:
    config = json.load(config_file)

debug = config["debug"]
version = config["version"]

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], use_pages=True)

pages = [dbc.ListGroupItem(page["name"], href=page["path"]) for page in dash.page_registry.values()]

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Home", href="/")),
        dbc.DropdownMenu(
            children=[dbc.DropdownMenuItem("Pages", header=True), *pages],
            nav=True,
            in_navbar=True,
            label="More",
        ),
    ],
    brand=f"eDAVE v{version}",
    brand_href="/",
    color="primary",
    dark=True,
)

app.layout = dbc.Container([navbar, dash.page_container], fluid=True)


if __name__ == "__main__":
    app.run_server(debug=debug)
