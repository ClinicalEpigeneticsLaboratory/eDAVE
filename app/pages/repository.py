import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html
from src.utils import load_config

config = load_config()
repository_summary = pd.read_pickle(config["summary_metafile"])


def plot(cnt: pd.Series, plot_type: str = None) -> go.Figure:
    """
    Function to generate Bar o Pie plot.

    :param cnt:
    :param plot_type:
    :return fig:
    """
    if plot_type == "bar":
        cnt = cnt.iloc[:15]
        fig = px.bar(cnt, y=cnt.index, x=cnt.values, orientation="h")
        fig.update_layout(
            xaxis={"title": "Count"},
            yaxis={"title": ""},
            font={"size": 15},
        )

    else:
        fig = px.pie(cnt, names=cnt.index, values=cnt.values)
        fig.update_layout(font={"size": 15})

    return fig


dash.register_page(__name__)

layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(
                dcc.Markdown(
                    f"""
                    ### Data repository details

                    ----

                    ###### Last update: {repository_summary["last_update"]}
                    ###### Total number of samples: {repository_summary["number_of_samples"]}
                    ###### Total number of categories: {repository_summary["number_of_samples_groups"]}

                    ----
                    """
                )
            ),
        ),
        dbc.Row(
            [
                dbc.Col("Current sample sheet: "),
                html.Br(),
                dbc.Col(dbc.Button("download CSV", id="download-sample-sheet-button", className="button-interact")),
                dcc.Download(id="download-sample-sheet-frame"),
            ]
        ),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Label("TOP 15 sample types by tissue or organ of origin"),
                        dcc.Graph(figure=plot(repository_summary["tissue_origin_cnt"], "bar")),
                    ],
                    xs=12,
                    sm=12,
                    md=6,
                    lg=6,
                    xl=6,
                ),
                dbc.Col(
                    [
                        dbc.Label("TOP 15 sample types by primary diagnosis"),
                        dcc.Graph(figure=plot(repository_summary["primary_diagnosis_cnt"], "bar")),
                    ],
                    xs=12,
                    sm=12,
                    md=6,
                    lg=6,
                    xl=6,
                ),
            ]
        ),
        html.Br(),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Label("Samples by tissue type"),
                        dcc.Graph(figure=plot(repository_summary["sample_type_cnt"])),
                    ],
                    xs=12,
                    sm=12,
                    md=6,
                    lg=6,
                    xl=6,
                ),
                dbc.Col(
                    [
                        dbc.Label("Samples by technology"),
                        dcc.Graph(figure=plot(repository_summary["exp_strategy_cnt"])),
                    ],
                    xs=12,
                    sm=12,
                    md=6,
                    lg=6,
                    xl=6,
                ),
            ]
        ),
    ],
    fluid=True, className="main-container"
)


@callback(
    Output("download-sample-sheet-frame", "data"),
    Input("download-sample-sheet-button", "n_clicks"),
    prevent_initial_call=True,
)
def sample_sheet_generator(n_clicks: int, sample_sheet_path: str = config["sample_sheet"]):
    """
    Function to generate sample sheet in csv format.

    :param n_clicks:
    :param sample_sheet_path:
    :return sample_sheet:
    """
    sample_sheet = pd.read_parquet(
        sample_sheet_path,
        columns=[
            "primary_diagnosis",
            "tissue_or_organ_of_origin",
            "sample_type",
            "experimental_strategy",
        ],
    )
    sample_sheet.index.name = "Case_ID"
    return dcc.send_data_frame(sample_sheet.to_csv, "sample_sheet.csv")
