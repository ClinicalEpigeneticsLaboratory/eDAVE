import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from src.utils import load_config

dash.register_page(__name__, path="/")
config = load_config()

card_1_content = [
    dbc.CardHeader("Tool"),
    dbc.CardBody(
        [
            html.H5("1-D browser", className="card-title"),
            html.P(
                "1-dimensional visualisation and statistical analysis of gene expression or CpG \
                methylation across various sample types.",
                className="card-text",
            ),
            dbc.Button("Go", href="/one-dimensional-browser", className="mt-auto"),
        ]
    ),
]

card_2_content = [
    dbc.CardHeader("Tool"),
    dbc.CardBody(
        [
            html.H5("M-D browser", className="card-title"),
            html.P(
                "Multidimensional visualisation of gene expression or CpG \
                methylation across various sample types.",
                className="card-text",
            ),
            dbc.Button("Go", href="/multi-dimensional-browser", className="mt-auto"),
        ]
    ),
]

card_3_content = [
    dbc.CardHeader("Tool"),
    dbc.CardBody(
        [
            html.H5("Association browser", className="card-title"),
            html.P(
                "Analysis of association between CpG methylation and gene expression\
                 in specific sample type.",
                className="card-text",
            ),
            dbc.Button("Go", href="/association-browser", className="mt-auto"),
        ]
    ),
]

card_4_content = [
    dbc.CardHeader("Tool"),
    dbc.CardBody(
        [
            html.H5("Differential features browser", className="card-title"),
            html.P(
                "Module to identify differential expressed genes (DEGs) or differential methylated positions (DMPs) \
                 between groups of samples.",
                className="card-text",
            ),
            dbc.Button("Go", href="/differential-features-browser", className="mt-auto"),
        ]
    ),
]

card_5_content = [
    dbc.CardHeader("Info"),
    dbc.CardBody(
        [
            html.H5("About repository", className="card-title"),
            html.P(
                "Details about repository, number of samples, sequencing platforms, last update etc.",
                className="card-text",
            ),
            dbc.Button("Read more", href="/repository", className="mt-auto", color="info"),
        ]
    ),
]

card_6_content = [
    dbc.CardHeader("Info"),
    dbc.CardBody(
        [
            html.H5("About us", className="card-title"),
            html.P(
                "More information about our department as well as contact details.",
                className="card-text",
            ),
            dbc.Button("Read more", href=config["footer_link"], className="mt-auto", color="info"),
        ]
    ),
]


layout = dbc.Container(
    [
        html.Br(),
        dbc.Container(
            dcc.Markdown(
                "### eDAVE - extension of GDC Data Analysis, Visualization, and Exploration Tools"
            ),
            style={"justifyContent": "center"},
        ),
        html.Br(),
        dbc.Container(
            dcc.Markdown(
                """
                 ----
                This app is an extension of
                GDC Data Analysis, Visualization, and Exploration [[DAVE]]
                (https://gdc.cancer.gov/analyze-data/gdc-dave-tools) tools.
                Designed for the exploration of publicly available **CpG methylation** or **gene expression** datasets.

                Importantly all data records in the current repository are coming from **Genome Data common**
                [database](https://gdc.cancer.gov/) and were obtained using state-of-the-art technologies.
                All records were processed in one, standardized way (raw data processing pipelines described in
                details [here](https://docs.gdc.cancer.gov/Data/Introduction/)), thus downstream analysis should be free
                of unwanted technical variance.

                 ----
                """
            ),
            style={"justifyContent": "center"},
        ),
        dbc.Row(html.Br()),
        dbc.Row(
            dbc.CardGroup(
                [
                    dbc.Card(card_1_content, color="danger", outline=True),
                    dbc.Card(card_2_content, color="danger", outline=True),
                    dbc.Card(card_3_content, color="danger", outline=True),
                ],
                style={"width": "75%"},
            ),
            justify="center",
        ),
        dbc.Row(
            dbc.CardGroup(
                [
                    dbc.Card(card_4_content, color="danger", outline=True),
                    dbc.Card(card_5_content, color="info", outline=True),
                    dbc.Card(card_6_content, color="info", outline=True),
                ],
                style={"width": "75%"},
            ),
            justify="center",
        ),
        dbc.Row(style={"height": "15vh"}),
    ],
    fluid=True,
)
