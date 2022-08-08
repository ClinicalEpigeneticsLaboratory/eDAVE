import typing as t

import dash
from src.basics import FrameOperations
from src.plots import Plot
from src.statistics import Stats
from src.utils import load_config

dash.register_page(__name__)

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, callback, dcc, html

EmptyFig = {}
config = load_config()
global_metadata = pd.read_pickle(config["global_metadata"])

layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label("Select data type", htmlFor="data-type-1d-browser"),
                        dcc.Dropdown(
                            id="data-type-1d-browser",
                            options=["Methylation [450K/EPIC]", "Expression [RNA-seq]"],
                            clearable=True,
                            multi=False,
                            value="",
                        ),
                    ],
                    width=4,
                    style={"padding": "10px"},
                ),
                dbc.Col(
                    [
                        html.Label("Select sample type/s", htmlFor="sample-types-1d-browser"),
                        dcc.Dropdown(
                            id="sample-types-1d-browser",
                            options=[],
                            clearable=True,
                            placeholder="Firstly select data type",
                            multi=True,
                            disabled=True,
                        ),
                        dbc.FormText("maximum number of sample types is 5"),
                    ],
                    width=4,
                    style={"padding": "10px"},
                ),
                dbc.Col(
                    [
                        html.Label("Input variable", htmlFor="variable-1d-browser"),
                        dbc.Input(
                            id="variable-1d-browser",
                            disabled=True,
                            placeholder="Firstly select data type",
                            maxLength=10,
                            type="text",
                            value="",
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
                        html.Label("Select scaling method", htmlFor="scaling-method-1d-browser"),
                        dcc.Dropdown(
                            id="scaling-method-1d-browser",
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
                        html.Label("Select plot type", htmlFor="plot-type-1d-browser"),
                        dcc.Dropdown(
                            id="plot-type-1d-browser",
                            options=["Box", "Violin"],
                            value="Box",
                            multi=False,
                            clearable=True,
                        ),
                    ]
                ),
                dbc.Col([html.Br(), dbc.Button("Submit", id="submit-1d-browser")]),
            ]
        ),
        dbc.Row(
            dbc.Col(dbc.Spinner(html.Div(id="progress-1d-browser"), color="danger")),
            style={"padding": "10px", "marginBottom": "10px", "marginTop": "10px"},
        ),
        dbc.Row(
            dbc.Collapse(
                dbc.Card(
                    dbc.CardBody(html.P(id="msg-1d-browser", className="card-text")),
                    color="danger",
                    outline=True,
                ),
                id="msg-section-1d-browser",
            )
        ),
        dbc.Row(
            dbc.Collapse(
                [
                    dbc.Row(dcc.Graph(id="plot-1d-browser")),
                    dbc.Row(
                        [
                            html.Label("Sample count", htmlFor="count-table-1d-browser"),
                            dbc.Container(id="count-table-1d-browser"),
                        ]
                    ),
                    dbc.Row(
                        [
                            html.Label("Post-hoc", htmlFor="post-hoc-1d-browser"),
                            dbc.Container(id="post-hoc-1d-browser"),
                        ]
                    ),
                ],
                id="result-section-1d-browser",
                is_open=False,
            ),
        ),
    ],
    fluid=True,
)


@callback(
    Output("sample-types-1d-browser", "options"),
    Output("sample-types-1d-browser", "disabled"),
    Output("sample-types-1d-browser", "value"),
    Input("data-type-1d-browser", "value"),
)
def update_sample_type_options(
    sample_types: t.Union[t.List[str], str]
) -> t.Tuple[t.List[str], bool, str]:
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

        return options, False, ""

    return [], True, ""


@callback(
    Output("variable-1d-browser", "disabled"),
    Output("variable-1d-browser", "placeholder"),
    Input("data-type-1d-browser", "value"),
)
def update_input_field(data_type: str) -> t.Tuple[bool, str]:
    """
    Function to update input field.
    """
    if data_type == "Expression [RNA-seq]":
        return False, "Eg. PAX3"
    if data_type == "Methylation [450K/EPIC]":
        return False, "Eg. cg07779434"

    return True, "Firstly select data type"


@callback(
    Output("result-section-1d-browser", "is_open"),
    Output("plot-1d-browser", "figure"),
    Output("msg-section-1d-browser", "is_open"),
    Output("msg-1d-browser", "children"),
    Output("post-hoc-1d-browser", "children"),
    Output("count-table-1d-browser", "children"),
    Output("progress-1d-browser", "children"),
    State("sample-types-1d-browser", "value"),
    State("data-type-1d-browser", "value"),
    State("variable-1d-browser", "value"),
    State("scaling-method-1d-browser", "value"),
    State("plot-type-1d-browser", "value"),
    Input("submit-1d-browser", "n_clicks"),
)
def main_1d_browser(
    sample_types: t.Union[t.List[str], str],
    data_type: str,
    variable: str,
    scaling_method: str,
    plot_type: str,
    n_clicks: int,
):
    """
    Main function of current dashboard, returns plot for selected variable and sample types.txt
    Return empty figure if:
    a) len(sample_types) > 5
    b) variable is not in repository
    """

    if data_type and variable:

        if len(sample_types) > 5:
            return (
                False,
                EmptyFig,
                True,
                "Exceeded maximum number of sample types [n>5]",
                "",
                "",
                "",
            )

        loader = FrameOperations(data_type, sample_types)
        data, msg = loader.load_1d(variable)

        if data.empty:
            return False, EmptyFig, True, msg, "", "", ""

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

            return True, fig, True, msg, post_hoc_frame, count, ""

        return True, fig, True, msg, "Applicable only for > 1 sample groups", count, ""

    return False, EmptyFig, False, "", "", "", ""
