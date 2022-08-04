import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html
from src.utils import load_config

config = load_config()
repository_summary = pd.read_pickle(config["summary_metafile"])


def plot(cnt: pd.Series, plot_type: str = None) -> go.Figure:
    if plot_type == "bar":
        cnt = cnt.iloc[:15]
        fig = px.bar(cnt, y=cnt.index, x=cnt.values, orientation="h")
        fig.update_layout(
            height=600,
            width=600,
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
    children=[
        html.H1(),
        dbc.Row(
            dbc.Col(
                dcc.Markdown(
                    f"""
                    ### Data repository details

                    ----

                    ###### Repository last update: {repository_summary["last_update"]}
                    ###### Number of samples in repository: {repository_summary["number_of_samples"]}
                    ###### Number of sample groups in repository: {repository_summary["number_of_samples_groups"]}

                    ----
                    """
                ),
            )
        ),
        html.Br(),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Label("TOP15 sample types by tissue or organ of origin"),
                        dcc.Graph(figure=plot(repository_summary["tissue_origin_cnt"], "bar")),
                    ]
                ),
                dbc.Col(
                    [
                        dbc.Label("TOP15 sample types by primary diagnosis"),
                        dcc.Graph(figure=plot(repository_summary["primary_diagnosis_cnt"], "bar")),
                    ]
                ),
            ]
        ),
        dbc.Row(),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Label("Samples by tissue type"),
                        dcc.Graph(figure=plot(repository_summary["sample_type_cnt"])),
                    ]
                ),
                dbc.Col(
                    [
                        dbc.Label("Samples by technology"),
                        dcc.Graph(figure=plot(repository_summary["exp_strategy_cnt"])),
                    ]
                ),
            ]
        ),
    ]
)
