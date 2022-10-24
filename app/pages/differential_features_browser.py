import logging
import typing as t

import dash

logger = logging.getLogger(__name__)
dash.register_page(__name__)

import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
from dash import Input, Output, State, callback, dcc, html
from src.basics import FrameOperations
from src.differential_features import DifferentialFeatures
from src.plots import Plot
from src.statistics import Stats
from src.utils import load_config

EmptyFig = {}
config = load_config()
global_metadata = pd.read_pickle(config["global_metadata"])

layout = dbc.Container(
    [
        dbc.Row([html.Br(), html.H3("Differential features (DEGs / DMPs) browser"), html.Hr()]),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label("Data type", htmlFor="data-type-dfeatures-browser"),
                        dcc.Dropdown(
                            id="data-type-dfeatures-browser",
                            options=["Methylation [450K/EPIC]", "Expression [RNA-seq]"],
                            clearable=True,
                            multi=False,
                        ),
                    ],
                    xs=10,
                    sm=10,
                    md=4,
                    lg=4,
                    xl=4,
                ),
                dbc.Col(
                    [
                        html.Label("Group A", htmlFor="groupA-dfeatures-browser"),
                        dcc.Dropdown(
                            id="groupA-dfeatures-browser",
                            options=[],
                            clearable=True,
                            multi=False,
                            disabled=True,
                            optionHeight=100,
                        ),
                    ],
                    xs=10,
                    sm=10,
                    md=4,
                    lg=4,
                    xl=4,
                ),
                dbc.Col(
                    [
                        html.Label("Group B", htmlFor="groupB-dfeatures-browser"),
                        dcc.Dropdown(
                            id="groupB-dfeatures-browser",
                            options=[],
                            clearable=True,
                            multi=False,
                            disabled=True,
                            optionHeight=100,
                        ),
                    ],
                    xs=10,
                    sm=10,
                    md=4,
                    lg=4,
                    xl=4,
                ),
            ]
        ),
        dbc.Row(
            dbc.Col([html.Br(), dbc.Button("Submit", id="submit-dfeatures-browser")]),
        ),
        html.Br(),
        dbc.Row(dbc.Col(dbc.Spinner(html.Div(id="progress-dfeatures-browser"), color="danger"))),
        html.Br(),
        dbc.Row(
            dbc.Collapse(
                dbc.Card(
                    dbc.CardBody(html.P(id="msg-dfeatures-browser", className="card-text")),
                    color="danger",
                    outline=True,
                ),
                id="msg-section-dfeatures-browser",
            )
        ),
        dbc.Row(
            dbc.Collapse(
                [
                    html.Br(),
                    dbc.Row(
                        dbc.Col(
                            [
                                dbc.Button(
                                    "download summary table", id="download-dfeatures-button"
                                ),
                                dcc.Download(id="download-dfeatures-frame"),
                            ],
                            xs=7,
                            sm=7,
                            md=7,
                            lg=7,
                            xl=7,
                        )
                    ),
                    dbc.Row(dcc.Graph(id="plot-dfeatures-browser")),
                    dbc.Row(
                        [
                            html.Label("Sample count", htmlFor="count-table-dfeatures-browser"),
                            dbc.Container(id="count-table-dfeatures-browser"),
                        ]
                    ),
                ],
                id="result-section-dfeatures-browser",
                is_open=False,
            ),
        ),
        dbc.Row(style={"height": "15vh"}),
    ],
    fluid=True,
)


@callback(
    Output("groupA-dfeatures-browser", "disabled"),
    Output("groupA-dfeatures-browser", "options"),
    Output("groupA-dfeatures-browser", "value"),
    Output("groupB-dfeatures-browser", "disabled"),
    Output("groupB-dfeatures-browser", "options"),
    Output("groupB-dfeatures-browser", "value"),
    Input("data-type-dfeatures-browser", "value"),
)
def update_groups_options(
    data_type: str,
) -> t.Tuple[bool, t.List[str], str, bool, t.List[str], str]:
    """
    Function to update possible sample types for selected data type.
    """
    if data_type:
        if data_type == "Expression [RNA-seq]":
            options = global_metadata["Expression_files_present"]
        elif data_type == "Methylation [450K/EPIC]":
            options = global_metadata["Methylation_files_present"]
        else:
            options = []

        return False, options, "", False, options, ""

    return True, [], "", True, [], ""


@callback(
    Output("download-dfeatures-frame", "data"),
    State("data-type-dfeatures-browser", "value"),
    State("groupA-dfeatures-browser", "value"),
    State("groupB-dfeatures-browser", "value"),
    Input("download-dfeatures-button", "n_clicks"),
    prevent_initial_call=True,
)
def func(data_type: str, group_A: str, group_B: str, n_clicks: int):
    path = f"temp/{data_type.replace('/', '_')}_{group_A}_{group_B}.parquet"
    frame = pd.read_parquet(path)

    return dcc.send_data_frame(frame.to_csv, "summary_table.csv")


@callback(
    Output("plot-dfeatures-browser", "figure"),
    Output("result-section-dfeatures-browser", "is_open"),
    Output("msg-dfeatures-browser", "children"),
    Output("msg-section-dfeatures-browser", "is_open"),
    Output("progress-dfeatures-browser", "children"),
    Output("count-table-dfeatures-browser", "children"),
    State("data-type-dfeatures-browser", "value"),
    State("groupA-dfeatures-browser", "value"),
    State("groupB-dfeatures-browser", "value"),
    Input("submit-dfeatures-browser", "n_clicks"),
)
def main_dfeatures_browser(data_type: str, group_A: str, group_B: str, clicks: int):
    if data_type and group_A and group_B:

        if group_A == group_B:
            return (
                EmptyFig,
                False,
                "Can not compare two identical groups of samples.",
                True,
                "",
                "",
            )

        loader = FrameOperations(data_type, [group_A, group_B])
        data, sample_frame = loader.load_mvpf()

        diffF = DifferentialFeatures(data, sample_frame, group_A, group_B)
        diffF.run()
        diffF.build_statistics_frame()
        results = diffF.export(data_type, group_A, group_B)

        if results.empty:
            return EmptyFig, False, "No DMPs/DEGs identified.", True, "", ""

        plot = Plot(results, "log2(FC)", "-log10(p-value)", None, None)
        fig = plot.volcanoplot(x_border=1, y_border=-np.log10(0.05))

        count = Stats(sample_frame.to_frame(), "SampleType").get_factor_count
        return fig, True, "Status: done.", True, "", count

    return dash.no_update