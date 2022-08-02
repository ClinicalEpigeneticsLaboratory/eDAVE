import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/")

card_1_content = [
    dbc.CardHeader("Module 1"),
    dbc.CardBody(
        [
            html.H5("1-D browser", className="card-title"),
            html.P(
                "This tool allows to 1D visualisation and statistical analysis of gene expression or CpG \
                methylation across various sample types.",
                className="card-text",
            ),
            dbc.Button("Go", href="/1d-browser", className="mt-auto"),
        ]
    ),
]

card_2_content = [
    dbc.CardHeader("Module 2"),
    dbc.CardBody(
        [
            html.H5("M-D browser", className="card-title"),
            html.P(
                "This tool allows to multidimensional visualisation of gene expression or CpG \
                methylation across various sample types.",
                className="card-text",
            ),
            dbc.Button("Go", href="/multidimensional-browser", className="mt-auto"),
        ]
    ),
]

card_3_content = [
    dbc.CardHeader("Module 3"),
    dbc.CardBody(
        [
            html.H5("Association browser", className="card-title"),
            html.P(
                "This tool allows to analyse association between CpG methylation and gene expression across\
                 various sample types.",
                className="card-text",
            ),
            dbc.Button(
                "Go", href="/methylation-expresion-browser", className="mt-auto"
            ),
        ]
    ),
]

card_4_content = [
    dbc.CardHeader("Module 4"),
    dbc.CardBody(
        [
            html.H5("Repository", className="card-title"),
            html.P(
                "Details about current repository, number of samples, last update etc.",
                className="card-text",
            ),
            dbc.Button("Go", href="/repository", className="mt-auto"),
        ]
    ),
]

layout = html.Div(
    [
        html.Br(),
        html.Div(
            html.H4(
                "eDAVE: extension of GDC Data Analysis, Visualization, and Exploration Tools"
            ),
            style={"display": "flex", "justifyContent": "center"},
        ),
        html.Br(),
        html.Div(
            dcc.Markdown(
                """
                This tools is an extension of 
                [GDC Data Analysis, Visualization, and Exploration (DAVE) Tools](https://gdc.cancer.gov/analyze-data/gdc-dave-tools).
                \n
                ... some text here ...
                """
            ),
            style={"display": "flex", "justifyContent": "center"},
        ),
        html.Br(),
        dbc.Row(
            [
                dbc.Col(dbc.Card(card_1_content, color="danger", outline=True)),
                dbc.Col(dbc.Card(card_2_content, color="danger", outline=True)),
                dbc.Col(dbc.Card(card_3_content, color="danger", outline=True)),
            ],
            className="mb-4",
        ),
        dbc.Row(
            dbc.Col(
                dbc.Card(card_4_content, color="info", outline=True),
                width={"size": 4, "offset": 4},
            ),
        ),
    ]
)
