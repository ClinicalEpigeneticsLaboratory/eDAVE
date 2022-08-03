import typing as t

import dash

dash.register_page(__name__)

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback, callback_context, dcc, html
from src.basics import FrameOperations
from src.plots import Plot
from src.statistics import Stats
from src.utils import load_config

emptyFig = go.Figure()
config = load_config()
global_metadata = pd.read_pickle(config["global_metadata"])

layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label("Select data type"),
                        dcc.Dropdown(
                            id="data-type-1d-explorer",
                            options=["Methylation [450K/EPIC]", "Expression [RNA-seq]"],
                            clearable=True,
                            multi=False,
                        ),
                    ],
                    width=4,
                    style={"padding": "10px"},
                ),
                dbc.Col(
                    [
                        html.Label("Select sample type/s"),
                        dcc.Dropdown(
                            id="sample-types-1d-explorer",
                            options=[],
                            clearable=True,
                            placeholder="Firstly select data type",
                            multi=True,
                            disabled=True,
                        ),
                    ],
                    width=4,
                    style={"padding": "10px"},
                ),
                dbc.Col(
                    [
                        html.Label("Input variable"),
                        dbc.Input(
                            id="variable-1d-explorer",
                            disabled=True,
                            placeholder="Firstly select data type",
                            maxLength=10,
                            type="text",
                        ),
                    ],
                    width=4,
                    style={"padding": "10px"},
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label("Select scaling method"),
                        dcc.Dropdown(
                            id="scaling-method-1d-explorer",
                            options=["None", "Log10", "Log2", "Ln", "Standard scaling"],
                            clearable=True,
                            multi=False,
                            value="None",
                            placeholder="None (default)",
                        ),
                    ]
                ),
                dbc.Col(
                    [
                        html.Label("Select plot type"),
                        dcc.Dropdown(
                            id="plot-type-1d-explorer",
                            options=["Box", "Violin"],
                            value="Box",
                            multi=False,
                            clearable=True,
                        ),
                    ]
                ),
                dbc.Col([html.Br(), dbc.Button("Submit", id="submit-1d-explorer")]),
            ]
        ),
        dbc.Row(
            dbc.Col([dbc.Spinner(html.Div(id="progress-1d-explorer"), color="danger")]),
            style={"padding": "10px", "marginBottom": "10px", "marginTop": "10px"},
        ),
        dbc.Row(
            dbc.Collapse(
                [
                    dbc.Row(dbc.Container(id="msg-1d-explorer")),
                    dbc.Row(dcc.Graph(id="plot-1d-explorer")),
                    dbc.Row(
                        [
                            html.Label("Sample count"),
                            dbc.Container(id="count-table-1d-explorer"),
                        ]
                    ),
                    dbc.Row([html.Label("Post-hoc"), dbc.Container(id="post-hoc-1d-explorer")]),
                ],
                id="result-section-1d-explorer",
                is_open=False,
            ),
        ),
    ],
    fluid=True,
)


@callback(
    Output("sample-types-1d-explorer", "options"),
    Output("sample-types-1d-explorer", "placeholder"),
    Output("sample-types-1d-explorer", "disabled"),
    Input("data-type-1d-explorer", "value"),
)
def update_sample_type_options(
    sample_types: t.Union[t.List[str], str]
) -> t.Tuple[t.List[str], str, bool]:
    """
    Function to update possible sample types for selected data type.
    """
    if sample_types:
        if sample_types == "Expression [RNA-seq]":
            options = global_metadata["Expression_files_present"]
        elif sample_types == "Methylation [450K/EPIC]":
            options = global_metadata["Methylation_files_present"]
        else:
            options = []

        return options, "Select...", False
    else:
        return [], "Firstly select data type", True


@callback(
    Output("variable-1d-explorer", "disabled"),
    Output("variable-1d-explorer", "placeholder"),
    Input("data-type-1d-explorer", "value"),
)
def update_input_field(data_type: str) -> t.Tuple[bool, str]:
    """
    Function to update input field.
    """

    if data_type == "Expression [RNA-seq]":
        return False, "Eg. PAX3"
    elif data_type == "Methylation [450K/EPIC]":
        return False, "Eg. cg07779434"
    else:
        return True, "Firstly select data type"


@callback(
    Output("result-section-1d-explorer", "is_open"),
    Output("plot-1d-explorer", "figure"),
    Output("msg-1d-explorer", "children"),
    Output("post-hoc-1d-explorer", "children"),
    Output("count-table-1d-explorer", "children"),
    Output("progress-1d-explorer", "children"),
    Input("sample-types-1d-explorer", "value"),
    Input("data-type-1d-explorer", "value"),
    Input("variable-1d-explorer", "value"),
    Input("scaling-method-1d-explorer", "value"),
    Input("plot-type-1d-explorer", "value"),
    Input("submit-1d-explorer", "n_clicks"),
)
def update_figure(
    sample_types: t.Union[t.List[str], str],
    data_type: str,
    variable: str,
    scaling_method: str,
    plot_type: str,
    submit: int,
):
    button = [p["prop_id"] for p in callback_context.triggered][0]
    if "submit-1d-explorer" in button and data_type and variable:

        loader = FrameOperations(data_type, sample_types)
        data = loader.load_1d(variable)
        data = data.dropna()

        if data.empty:
            return (
                True,
                emptyFig,
                f"Variable {variable} not found in requested repository",
                "",
                "",
                "",
            )

        data[variable] = loader.scale(data[variable], scaling_method)
        figureGenerator = Plot(
            data,
            x_axis="SampleType",
            y_axis=variable,
            scaling_method=scaling_method,
            data_type=data_type,
        )

        if plot_type == "Box":
            fig = figureGenerator.boxplot()
        else:
            fig = figureGenerator.violinplot()

        stats = Stats(data, "SampleType")
        count = stats.get_factor_count

        if len(sample_types) > 1:
            stats.post_hoc()
            post_hoc_frame = stats.export_frame()

            return True, fig, "Status: done", post_hoc_frame, count, ""

        return (
            True,
            fig,
            "Status: done",
            "Applicable only for > 1 sample groups.",
            stats.get_factor_count,
            "",
        )

    else:
        return False, emptyFig, "", "", "", ""
