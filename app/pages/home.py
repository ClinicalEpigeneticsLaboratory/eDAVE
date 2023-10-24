import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from src.utils import load_config, load_news

dash.register_page(__name__, path="/")
config = load_config()
news = load_news()

card_1_content = [
    dbc.CardHeader("Tool", className="text-align"),
    dbc.CardBody(
        [
            html.H5(
                "Differential features (DEGs/DMPs) explorer", className="card-title text-align"
            ),
            html.P(
                "Identification of differentially expressed genes (DEGs) or differentially methylated positions (DMPs) \
                 between groups of samples.",
                className="card-text text-align",
            ),
            dbc.Button(
                "Go",
                href="/differential-features-explorer",
                className="button-home-style button-interact",
            ),
        ],
    ),
]

card_2_content = [
    dbc.CardHeader("Tool", className="text-align"),
    dbc.CardBody(
        [
            html.H5("Single probe/gene explorer", className="card-title text-align"),
            html.P(
                "One-dimensional visualisation and statistical analysis of gene expression or CpG \
                methylation across various samples types.",
                className="card-text text-align",
            ),
            dbc.Button(
                "Go", href="/probe-gene-explorer", className="button-home-style button-interact"
            ),
        ],
    ),
]

card_3_content = [
    dbc.CardHeader("Tool", className="text-align"),
    dbc.CardBody(
        [
            html.H5("Cluster explorer", className="card-title text-align"),
            html.P(
                "Multidimensional visualisation and cluster analysis of genes expression or CpGs \
                methylation across various samples types.",
                className="card-text text-align",
            ),
            dbc.Button(
                "Go", href="/cluster-explorer", className="button-home-style button-interact"
            ),
        ],
    ),
]

card_4_content = [
    dbc.CardHeader("Tool", className="text-align"),
    dbc.CardBody(
        [
            html.H5(
                "Methylation-expression association explorer", className="card-title text-align"
            ),
            html.P(
                "Analysis of association between CpG methylation and gene expression\
                 within a specific sample type.",
                className="card-text text-align",
            ),
            dbc.Button(
                "Go", href="/association-explorer", className="button-home-style button-interact"
            ),
        ],
    ),
]

card_5_content = [
    dbc.CardHeader("Info", className="text-align"),
    dbc.CardBody(
        [
            html.H5("About repository", className="card-title text-align"),
            html.P(
                "Details about repository, number of samples, types of measurement technologies, last update etc.",
                className="card-text text-align",
            ),
            dbc.Button(
                "Read more",
                href="/repository",
                className="button-home-style button-interact",
                color="info",
            ),
        ],
    ),
]

card_6_content = [
    dbc.CardHeader("Info", className="text-align"),
    dbc.CardBody(
        [
            html.H5("Documentation", className="card-title text-align"),
            html.P(
                "More information about eDAVE, materials, methods and assumptions.",
                className="card-text text-align",
            ),
            dbc.Button(
                "Read more",
                href="/documentation",
                className=" button-home-style button-interact",
                color="info",
            ),
        ],
    ),
]

layout = dbc.Container(
    [
        dbc.Row(html.Br()),
        dbc.Row(
            dbc.Col(
                dcc.Markdown(
                    "### **eDAVE** - **e**xtension of GDC **D**ata **A**nalysis, **V**isualization, and **E**xploration Tools",
                    style={"text-align": "center"},
                ),
                xs=12,
                sm=12,
                md=12,
                lg=12,
                xl=12,
            ),
            justify="center",
        ),
        dbc.Row(html.Br()),
        dbc.Row(
            dbc.Col(
                dcc.Markdown(
                    """
                    ----
                    This application was designed to enable user-friendly analysis and visualization of
                    methylomics and transcriptomics datasets deposited in the [Genomic Data Commons](https://gdc.cancer.gov/) 
                    repository.
    
                    If you want to report a bug or request a new feature, please use [GitHub](https://github.com/ClinicalEpigeneticsLaboratory/eDAVE/issues)
                    Contact: [Jan Bińkowski](mailto:jan.binkowski@pum.edu.pl)
                    ----
                    """,
                    style={"text-align": "center"},
                ),
                xs=12,
                sm=12,
                md=12,
                lg=12,
                xl=12,
            )
        ),
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader("News"),
                        dbc.CardBody(
                            dcc.Markdown(f"{news}"),
                        ),
                    ],
                    outline=True,
                    color="info",
                ),
                xs=12,
                sm=12,
                md=12,
                lg=12,
                xl=12,
            ),
            justify="center",
        ),
        dbc.Row(html.Br()),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(card_1_content, className="card-style-custom"),
                    xs=12,
                    sm=12,
                    md=4,
                    lg=4,
                    xl=4,
                ),
                dbc.Col(
                    dbc.Card(card_2_content, className="card-style-custom"),
                    xs=12,
                    sm=12,
                    md=4,
                    lg=4,
                    xl=4,
                ),
                dbc.Col(
                    dbc.Card(card_3_content, className="card-style-custom"),
                    xs=12,
                    sm=12,
                    md=4,
                    lg=4,
                    xl=4,
                ),
            ],
            justify="center",
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(card_4_content, className="card-style-custom"),
                    xs=12,
                    sm=12,
                    md=4,
                    lg=4,
                    xl=4,
                ),
                dbc.Col(
                    dbc.Card(card_5_content, className="card-style-custom"),
                    xs=12,
                    sm=12,
                    md=4,
                    lg=4,
                    xl=4,
                ),
                dbc.Col(
                    dbc.Card(card_6_content, className="card-style-custom"),
                    xs=12,
                    sm=12,
                    md=4,
                    lg=4,
                    xl=4,
                ),
            ],
            justify="center",
        ),
    ],
    fluid=True,
    className="main-container",
)
