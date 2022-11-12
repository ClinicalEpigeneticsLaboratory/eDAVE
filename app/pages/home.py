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
            html.H5("Differential features browser", className="card-title"),
            html.P(
                "Module to identify differentially expressed genes (DEGs) or differentially methylated positions (DMPs) \
                 between groups of samples.",
                className="card-text",
            ),
            dbc.Button("Go", href="/differential-features-browser", className="mt-auto"),
        ]
    ),
]

card_2_content = [
    dbc.CardHeader("Tool"),
    dbc.CardBody(
        [
            html.H5("1-D browser", className="card-title"),
            html.P(
                "One-dimensional visualisation and statistical analysis of gene expression or CpG \
                methylation across various samples types.",
                className="card-text",
            ),
            dbc.Button("Go", href="/one-dimensional-browser", className="mt-auto"),
        ]
    ),
]

card_3_content = [
    dbc.CardHeader("Tool"),
    dbc.CardBody(
        [
            html.H5("M-D browser", className="card-title"),
            html.P(
                "Multidimensional visualisation and cluster analysis of genes expression or CpGs \
                methylation across various samples types.",
                className="card-text",
            ),
            dbc.Button("Go", href="/multi-dimensional-browser", className="mt-auto"),
        ]
    ),
]

card_4_content = [
    dbc.CardHeader("Tool"),
    dbc.CardBody(
        [
            html.H5("Association browser", className="card-title"),
            html.P(
                "Analysis of association between CpG methylation and gene expression\
                 within a specific sample type.",
                className="card-text",
            ),
            dbc.Button("Go", href="/association-browser", className="mt-auto"),
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
            html.H5("Documentation", className="card-title"),
            html.P(
                "More information about eDAVE, materials, methods and assumptions.",
                className="card-text",
            ),
            dbc.Button("Read more", href="/documentation", className="mt-auto", color="info"),
        ]
    ),
]


layout = dbc.Container(
    [
        dbc.Row(html.Br()),
        dbc.Row(
            dbc.Col(
                dcc.Markdown(
                    "### **eDAVE** - **e**xtension of GDC **D**ata **A**nalysis, **V**isualization, and **E**xploration Tools",
                ),
                xs=8,
                sm=8,
                md=8,
                lg=8,
                xl=8,
            ),
            justify="center",
        ),
        dbc.Row(html.Br()),
        dbc.Row(
            dbc.Col(
                dcc.Markdown(
                    """
                 ----
                This app is an extension of
                GDC Data Analysis, Visualization, and Exploration [[DAVE]]
                (https://gdc.cancer.gov/analyze-data/gdc-dave-tools) tools.
                Designed for the exploration of publicly available **methylomics** and **transcriptomics** datasets.

                Importantly, all data records in the current repository are coming from **Genome Data common**
                [database](https://gdc.cancer.gov/) and were obtained using state-of-the-art technologies.
                All records were processed in one, standardized way (raw data processing pipelines described in
                details [here](https://docs.gdc.cancer.gov/Data/Introduction/)), thus downstream analysis should be free
                of unwanted technical variance.

                Contact: [Jan Bińkowski](mailto:jan.binkowski@pum.edu.pl)
                 ----
                """
                ),
                xs=10,
                sm=10,
                md=10,
                lg=10,
                xl=10,
            ),
            justify="center",
        ),
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader("News"),
                        dbc.CardBody(
                            dcc.Markdown(
                                """
                                * 12.11.2022: Added *news* section;
                                * 12.11.2022: Added transformation method in association browser;
                                """
                            ),
                        ),
                    ],
                    outline=True,
                    color="info",
                ),
                xs=10,
                sm=10,
                md=10,
                lg=10,
                xl=10,
            ),
            justify="center",
        ),
        dbc.Row(html.Br()),
        dbc.Row(
            dbc.Col(
                dbc.CardGroup(
                    [
                        dbc.Card(card_1_content, color="danger", outline=True),
                        dbc.Card(card_2_content, color="danger", outline=True),
                        dbc.Card(card_3_content, color="danger", outline=True),
                    ],
                ),
                xs=10,
                sm=10,
                md=10,
                lg=10,
                xl=10,
            ),
            justify="center",
        ),
        dbc.Row(
            dbc.Col(
                dbc.CardGroup(
                    [
                        dbc.Card(card_4_content, color="danger", outline=True),
                        dbc.Card(card_5_content, color="danger", outline=True),
                        dbc.Card(card_6_content, color="danger", outline=True),
                    ],
                ),
                xs=10,
                sm=10,
                md=10,
                lg=10,
                xl=10,
            ),
            justify="center",
        ),
        dbc.Row(style={"height": "15vh"}),
    ],
    fluid=True,
)
