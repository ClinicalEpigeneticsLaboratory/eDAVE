import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

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
            dbc.Button("Go", href="/methylation-expresion-browser", className="mt-auto"),
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

layout = dbc.Container(
    [
        html.Br(),
        html.Div(
            html.H4("eDAVE: extension of GDC Data Analysis, Visualization, and Exploration Tools"),
            style={"display": "flex", "justifyContent": "center"},
        ),
        html.Br(),
        dbc.Container(
            dcc.Markdown(
                """
                This app is an extension of 
                GDC Data Analysis, Visualization, and Exploration [[DAVE]] 
                (https://gdc.cancer.gov/analyze-data/gdc-dave-tools) tools
                for quantitative traits such as DNA methylation and gene expression. 
                                 
                Importantly all data records in current repository are coming from **Genome Data common** 
                [database](https://gdc.cancer.gov/) and were obtained using the most prominent technologies 
                such as **Illumina microarrays** and **RNA-seq** and processed in one way 
                (raw data processing pipelines described in 
                detail [here](https://docs.gdc.cancer.gov/Data/Introduction/)). 
                Thus downstream analysis should be free of unwanted technical variance.
                """
            ),
            style={"justifyContent": "center"},
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
    ],
    fluid=True,
)
