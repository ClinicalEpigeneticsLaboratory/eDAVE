import json
import logging

import dash
import dash_bootstrap_components as dbc

with open("config.json", "r", encoding="UTF-8") as config_file:
    config = json.load(config_file)

debug = config["debug"]
version = config["version"]
link = config["footer_link"]
app_title = config["app_title"]

app = dash.Dash(
    __name__, external_stylesheets=[dbc.themes.FLATLY], use_pages=True, app_title=app_title
)
server = app.server

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

footer = dash.html.Footer(
    [
        dbc.Alert(
            [
                "Powered by ",
                dash.html.A(
                    "The Independent Clinical Epigenetics Laboratory",
                    href=link,
                    target="blank",
                    className="alert-link",
                ),
                ", for research use only.",
            ],
            color="primary",
        ),
    ],
    style={"bottom": "0", "width": "98%", "position": "fixed"},
)

app.layout = dbc.Container([navbar, dash.page_container, footer], fluid=True)

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    filename="log.log",
    level=logging.INFO,
    datefmt="%m/%d/%Y %I:%M:%S %p",
)

if __name__ == "__main__":
    app.run_server(debug=debug)
