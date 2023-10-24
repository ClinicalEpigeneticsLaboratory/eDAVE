import typing as t
import logging
import dash

logger = logging.getLogger(__name__)
dash.register_page(__name__)

import pandas as pd
import dash_loading_spinners as dls
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html
from src.basics import FrameOperations
from src.utils import load_config, send_slack_msg, temp_file_path

EmptyFig = {}
config = load_config()
global_metadata = pd.read_pickle(config["global_metadata"])

app = dash.get_app()

layout = dbc.Container(
    [
        dbc.Row([html.Br(), html.H3("Data explorer"), html.Hr()]),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label("Data type", htmlFor="data-type-downloader"),
                        dcc.Dropdown(
                            id="data-type-downloader",
                            options=["Methylation [450K/EPIC]", "Expression [RNA-seq]"],
                            clearable=True,
                            multi=False,
                        ),
                    ],
                    xs=12,
                    sm=12,
                    md=5,
                    lg=5,
                    xl=5,
                ),
                dbc.Col(
                    [
                        html.Label("Category", htmlFor="category-downloader"),
                        dcc.Dropdown(
                            id="category-downloader",
                            options=[],
                            clearable=True,
                            multi=False,
                            disabled=True,
                            placeholder="Firstly select a data type",
                            optionHeight=100,
                        ),
                        dbc.FormText("Select category to download."),
                    ],
                    xs=12,
                    sm=12,
                    md=5,
                    lg=5,
                    xl=5,
                ),
                dbc.Col(
                    [
                        html.Br(),
                        dbc.Button(
                            "Download dataset",
                            id="download-button-downloader",
                            color="danger",
                            className="button-interact",
                        ),
                        dcc.Download(id="download-dataset-downloader"),
                    ]
                ),
                dbc.Row(
                    dbc.Col(
                        dls.Hash(
                            html.Div(id="progress-downloader"),
                            color="#FF0000",
                            debounce=30,
                            speed_multiplier=2,
                            size=100,
                            fullscreen=True,
                            show_initially=False,
                        )
                    )
                ),
            ]
        ),
        html.Br(),
    ],
    fluid=True,
    className="main-container",
)


@callback(
    Output("category-downloader", "disabled"),
    Output("category-downloader", "options"),
    Output("category-downloader", "value"),
    Input("data-type-downloader", "value"),
    prevent_initial_call=True,
)
def update_groups_options(
    data_type: str,
) -> t.Tuple[bool, t.List[str], str]:
    """
    Function to update sample type options list based on selected data type.
    Returns the same list of options to field - group A and field - group B.

    :param data_type:
    :return boolean, options, str, boolean, options, str:
    """
    if data_type:
        if data_type == "Expression [RNA-seq]":
            options = global_metadata["Expression_files_present"]
        elif data_type == "Methylation [450K/EPIC]":
            options = global_metadata["Methylation_files_present"]
        else:
            options = []

        return False, options, ""

    return True, [], ""


@callback(
    Output("download-dataset-downloader", "data"),
    Output("progress-downloader", "children"),
    State("data-type-downloader", "value"),
    State("category-downloader", "value"),
    Input("download-button-downloader", "n_clicks"),
    prevent_initial_call=True,
)
def download_dataset(data_type: str, sample_type: str, _: int) -> t.Tuple[t.Any, str]:
    """
    Function to load and return a specific dataset from local data repository.

    :param data_type:
    :param sample_type:
    :param _:
    :return:
    """

    loader = FrameOperations(data_type, sample_type)

    dataset = loader.load_whole_dataset()
    name = f"{data_type} - {sample_type}"

    msg = f"Requested dataset: {name}"
    send_slack_msg("Datasets browser", msg)
    logger.info(msg)

    return dcc.send_data_frame(dataset.to_csv, f"{name}.csv"), ""
