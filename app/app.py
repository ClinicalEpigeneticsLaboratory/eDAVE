import logging

import dash
import dash_bootstrap_components as dbc
from src.utils import load_config

config = load_config()
debug = config["debug"]
version = config["version"]
link = config["footer_link"]
maintenance_page = config["maintenance_page"]

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    filename="log.log",
    level=logging.INFO,
    datefmt="%Y/%m/%d %I:%M:%S %p",
)

if maintenance_page:
    msg = """
    eDAVE is currently not available due to maintenance work, it will come back as soon as possible.
    Contact: jan.binkowski[at].pum.edu.pl
    """
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], use_pages=False)
    app.layout = dbc.Container(dash.html.H5(msg), fluid=True)
    server = app.server

else:
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], use_pages=True)
    server = app.server

    pages = [
        dbc.ListGroupItem(page["name"], href=page["path"]) for page in dash.page_registry.values()
    ]

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
        brand=f"eDAVE {version}",
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
                    ". For research use only.",
                ],
                color="primary",
            ),
        ],
        style={"bottom": "0", "width": "98%", "position": "fixed"},
    )

    app.layout = dbc.Container([navbar, dash.page_container, footer], fluid=True)


if __name__ == "__main__":
    app.run_server(debug=debug)
