import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

dash.register_page(__name__, path="/")

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
    dbc.CardHeader("Info"),
    dbc.CardBody(
        [
            html.H5("About repository", className="card-title"),
            html.P(
                "Details about repository, number of samples, last update etc.",
                className="card-text",
            ),
            dbc.Button("Read more", href="/repository", className="mt-auto", color="info"),
        ]
    ),
]

layout = dbc.Container(
    [
        html.Br(),
        html.Div(
            dcc.Markdown(
                "### eDAVE - extension of GDC Data Analysis, Visualization, and Exploration Tools"
            ),
            style={"display": "flex", "justifyContent": "center"},
        ),
        html.Br(),
        dbc.Container(
            dcc.Markdown(
                """
                 ----
                This app is an extension of
                GDC Data Analysis, Visualization, and Exploration [[DAVE]]
                (https://gdc.cancer.gov/analyze-data/gdc-dave-tools) tools.
                Dedicated to analysing quantitative assays such as DNA methylation and/or gene expression.

                Importantly all data records in the current repository are coming from **Genome Data common**
                [database](https://gdc.cancer.gov/) and were obtained using state-of-the-art technologies,
                such as: **Illumina microarrays** and **RNA-seq**. All records were processed in one, standardized way
                (raw data processing pipelines described in
                detail [here](https://docs.gdc.cancer.gov/Data/Introduction/)),
                thus downstream analysis should be free of unwanted technical variance.

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
                ],
                style={"width": "75%"},
            ),
            justify="center",
        ),
        dbc.Row(
            dbc.CardGroup(
                [
                    dbc.Card(card_3_content, color="danger", outline=True),
                    dbc.Card(card_4_content, color="info", outline=True),
                ],
                style={"width": "75%"},
            ),
            justify="center",
        ),
        dbc.Row(style={"height": "15vh"}),
    ],
    fluid=True,
)
