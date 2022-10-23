import logging
import typing as t

import dash

logger = logging.getLogger(__name__)
dash.register_page(__name__)

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, callback, dcc, html
from src.basics import FrameOperations
from src.plots import Plot
from src.statistics import Stats
from src.utils import load_config

EmptyFig = {}
config = load_config()
global_metadata = pd.read_pickle(config["global_metadata"])

layout = dbc.Container(
    [
        dbc.Row([html.Br(), html.H3("One dimensional browser"), html.Hr()]),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label("Data type", htmlFor="data-type-1d-browser"),
                        dcc.Dropdown(
                            id="data-type-1d-browser",
                            options=["Methylation [450K/EPIC]", "Expression [RNA-seq]"],
                            clearable=True,
                            multi=False,
                            value="",
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
                        html.Label("Sample type/s", htmlFor="sample-types-1d-browser"),
                        dcc.Dropdown(
                            id="sample-types-1d-browser",
                            options=[],
                            clearable=True,
                            placeholder="Firstly select a data type",
                            multi=True,
                            disabled=True,
                            optionHeight=100,
                        ),
                        dbc.FormText("maximum number of samples types is 5"),
                    ],
                    xs=10,
                    sm=10,
                    md=4,
                    lg=4,
                    xl=4,
                ),
                dbc.Col(
                    [
                        html.Label(
                            "Probe ID/Gene",
                            htmlFor="variable-1d-browser",
                            id="label-cpg-gene-1d-browser",
                            style={
                                "color": "blue",
                                "textDecoration": "underline",
                                "cursor": "pointer",
                            },
                        ),
                        dbc.Tooltip(
                            "Gene name is case sensitive. "
                            "Probe ID is a unique identifier from appropriate [EPIC/450K] Illumina manifest.",
                            target="label-cpg-gene-1d-browser",
                            placement="top",
                        ),
                        dbc.Input(
                            id="variable-1d-browser",
                            disabled=True,
                            placeholder="Firstly select a data type",
                            maxLength=10,
                            type="text",
                            value="",
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
            [
                dbc.Col(
                    [
                        html.Label("Scaling method", htmlFor="scaling-method-1d-browser"),
                        dcc.Dropdown(
                            id="scaling-method-1d-browser",
                            options=["None", "Log10", "Log2", "Ln", "Standard scaling"],
                            clearable=True,
                            multi=False,
                            value="None",
                            placeholder="None (default)",
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
                        html.Label("Plot type", htmlFor="plot-type-1d-browser"),
                        dcc.Dropdown(
                            id="plot-type-1d-browser",
                            options=["Box", "Violin", "Scatter"],
                            value="Box",
                            multi=False,
                            clearable=True,
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
                        html.Label("Alpha (significance level)", htmlFor="alpha-type-1d-browser"),
                        dcc.Slider(
                            0.001,
                            0.1,
                            0.001,
                            value=0.05,
                            tooltip={"placement": "bottom", "always_visible": True},
                            marks=None,
                            id="alpha-type-1d-browser",
                        ),
                    ],
                    xs=10,
                    sm=10,
                    md=4,
                    lg=4,
                    xl=4,
                ),
                dbc.Col(
                    [html.Br(), dbc.Button("Submit", id="submit-1d-browser")],
                    xs=10,
                    sm=10,
                    md=6,
                    lg=6,
                    xl=6,
                ),
            ]
        ),
        html.Br(),
        dbc.Row(dbc.Col(dbc.Spinner(html.Div(id="progress-1d-browser"), color="danger"))),
        html.Br(),
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
        dbc.Row(style={"height": "15vh"}),
    ],
    fluid=True,
)


@callback(
    Output("sample-types-1d-browser", "options"),
    Output("sample-types-1d-browser", "disabled"),
    Output("sample-types-1d-browser", "value"),
    Output("variable-1d-browser", "value"),
    Input("data-type-1d-browser", "value"),
)
def update_sample_type_options(
    data_type: t.Union[t.List[str], str]
) -> t.Tuple[t.List[str], bool, str, str]:
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

        return options, False, "", ""

    return [], True, "", ""


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
        return False, "E.g. PAX3"
    if data_type == "Methylation [450K/EPIC]":
        return False, "E.g. cg07779434"

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
    State("alpha-type-1d-browser", "value"),
    Input("submit-1d-browser", "n_clicks"),
)
def main_1d_browser(
    sample_types: t.Union[t.List[str], str],
    data_type: str,
    variable: str,
    scaling_method: str,
    plot_type: str,
    alpha: float,
    n_clicks: int,
):
    if data_type and variable:
        if len(sample_types) > 5:
            logger.info("Aborted: exceeded maximum number of sample types > 5.")
            return (
                False,
                EmptyFig,
                True,
                "Exceeded maximum number of sample types [n>5].",
                "",
                "",
                "",
            )

        loader = FrameOperations(data_type, sample_types)
        data, msg = loader.load_1d(variable)

        if data.empty:
            logger.info("Aborted: data records for this specific requests are not available.")
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
        elif plot_type == "Violin":
            fig = figureGenerator.violinplot()
        else:
            fig = figureGenerator.scatterplot()

        stats = Stats(data, "SampleType", alpha=alpha)
        count = stats.get_factor_count

        if len(sample_types) > 1:
            stats.test_for_variance_heterogeneity(variable)
            stats.post_hoc(variable)
            post_hoc_frame = stats.export_frame()

            logger.info(
                f"Input: {sample_types} - {data_type} - {variable} - {scaling_method} - {plot_type}"
            )
            return True, fig, True, msg, post_hoc_frame, count, ""

        logger.info(
            f"Input: {sample_types} - {data_type} - {variable} - {scaling_method} - {plot_type}"
        )
        return True, fig, True, msg, "Applicable only for > 1 sample types.", count, ""

    return dash.no_update
