import logging
import typing as t

import dash
import diskcache

logger = logging.getLogger(__name__)
dash.register_page(__name__)

import dash_bootstrap_components as dbc
import dash_loading_spinners as dls
import numpy as np
import pandas as pd
from dash import Input, Output, State, callback, dcc, html
from dash.long_callback import DiskcacheLongCallbackManager
from src.basics import FrameOperations
from src.differential_features import DifferentialFeatures
from src.plots import Plot
from src.statistics import Stats
from src.utils import load_config, send_slack_msg, temp_file_path

EmptyFig = {}
config = load_config()
global_metadata = pd.read_pickle(config["global_metadata"])

app = dash.get_app()
cache = diskcache.Cache("./cache")
long_callback_manager = DiskcacheLongCallbackManager(cache)

layout = dbc.Container(
    [
        dbc.Row([html.Br(), html.H3("Differential features (DEGs/DMPs) explorer"), html.Hr()]),
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
                    xs=12,
                    sm=12,
                    md=4,
                    lg=4,
                    xl=4,
                ),
                dbc.Col(
                    [
                        html.Label("Category A", htmlFor="groupA-dfeatures-browser"),
                        dcc.Dropdown(
                            id="groupA-dfeatures-browser",
                            options=[],
                            clearable=True,
                            multi=False,
                            disabled=True,
                            placeholder="Firstly select a data type",
                            optionHeight=100,
                        ),
                        dbc.FormText("Select category A to perform comparison."),
                    ],
                    xs=12,
                    sm=12,
                    md=4,
                    lg=4,
                    xl=4,
                ),
                dbc.Col(
                    [
                        html.Label("Category B", htmlFor="groupB-dfeatures-browser"),
                        dcc.Dropdown(
                            id="groupB-dfeatures-browser",
                            options=[],
                            clearable=True,
                            multi=False,
                            disabled=True,
                            placeholder="Firstly select a data type",
                            optionHeight=100,
                        ),
                        dbc.FormText("Select category B to perform comparison."),
                    ],
                    xs=12,
                    sm=12,
                    md=4,
                    lg=4,
                    xl=4,
                ),
            ]
        ),
        html.Br(),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label(
                            "Alpha (significance level)",
                            htmlFor="alpha-dfeatures-browser",
                            id="label-alpha-df-explorer",
                            className="tooltip-style",
                        ),
                        dbc.Tooltip(
                            "eDAVE uses raw p-value for normality and homoscedasticity assessment and FDR-corrected "
                            "for DEG/DMPs identification.",
                            target="label-alpha-df-explorer",
                            placement="top",
                        ),
                        dcc.Slider(
                            0.001,
                            0.1,
                            0.001,
                            value=0.05,
                            tooltip={"placement": "bottom", "always_visible": True},
                            marks=None,
                            id="alpha-dfeatures-browser",
                        ),
                    ],
                    xs=12,
                    sm=12,
                    md=4,
                    lg=4,
                    xl=4,
                ),
                dbc.Col(
                    [
                        html.Label("Minimum effect size", htmlFor="min-effect-dfeatures-browser"),
                        dcc.Slider(
                            0,
                            0,
                            0,
                            value=0.05,
                            tooltip={"placement": "bottom", "always_visible": True},
                            marks=None,
                            disabled=True,
                            id="min-effect-dfeatures-browser",
                        ),
                        dbc.FormText(
                            "Effect size is expressed as |log2(FC)| for expression and |delta| for methylation datasets."
                        ),
                    ],
                    xs=12,
                    sm=12,
                    md=4,
                    lg=4,
                    xl=4,
                ),
                dbc.Col(
                    [
                        html.Br(),
                        dbc.Button(
                            "Submit", id="submit-dfeatures-browser", className="button-interact"
                        ),
                    ]
                ),
            ],
        ),
        html.Br(),
        dbc.Row(
            dbc.Col(
                dls.Hash(
                    html.Div(id="progress-dfeatures-browser"),
                    color="#FF0000",
                    debounce=30,
                    speed_multiplier=2,
                    size=100,
                    fullscreen=True,
                    show_initially=False,
                )
            )
        ),
        html.Br(),
        dbc.Row(
            dbc.Collapse(
                dbc.Card(
                    dbc.CardBody(html.P(id="msg-dfeatures-browser")),
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
                        [
                            dbc.Col(
                                dcc.Graph(
                                    id="plot-dfeatures-browser",
                                    config={
                                        "toImageButtonOptions": {
                                            "format": "svg",
                                            "filename": "volcano_plot",
                                            "height": 500,
                                            "width": 700,
                                            "scale": 2,
                                        },
                                        "displayModeBar": True,
                                    },
                                ),
                                xs=11,
                                sm=11,
                                md=6,
                                lg=6,
                                xl=6,
                            ),
                            dbc.Col(
                                dcc.Graph(
                                    id="cnt-plot-dfeatures-browser",
                                    config={
                                        "toImageButtonOptions": {
                                            "format": "svg",
                                            "filename": "pie_plot",
                                            "height": 500,
                                            "width": 700,
                                            "scale": 2,
                                        },
                                        "displayModeBar": True,
                                    },
                                ),
                                xs=11,
                                sm=11,
                                md=6,
                                lg=6,
                                xl=6,
                            ),
                        ]
                    ),
                    html.Br(),
                    dbc.Row(
                        [
                            dbc.Button(
                                "download summary table",
                                id="download-dfeatures-button",
                                color="danger",
                            ),
                            dcc.Download(id="download-dfeatures-frame"),
                        ],
                    ),
                    html.Br(),
                    dbc.Row(
                        [
                            html.Label(
                                "Sample count frame", htmlFor="count-table-dfeatures-browser"
                            ),
                            dbc.Container(id="count-table-dfeatures-browser"),
                        ]
                    ),
                ],
                id="result-section-dfeatures-browser",
                is_open=False,
            ),
        ),
    ],
    fluid=True,
    className="main-container",
)


@callback(
    Output("groupA-dfeatures-browser", "disabled"),
    Output("groupA-dfeatures-browser", "options"),
    Output("groupA-dfeatures-browser", "value"),
    Output("groupB-dfeatures-browser", "disabled"),
    Output("groupB-dfeatures-browser", "options"),
    Output("groupB-dfeatures-browser", "value"),
    Input("data-type-dfeatures-browser", "value"),
    prevent_initial_call=True,
)
def update_groups_options(
    data_type: str,
) -> t.Tuple[bool, t.List[str], str, bool, t.List[str], str]:
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

        return False, options, "", False, options, ""

    return True, [], "", True, [], ""


@callback(
    Output("min-effect-dfeatures-browser", "disabled"),
    Output("min-effect-dfeatures-browser", "min"),
    Output("min-effect-dfeatures-browser", "max"),
    Output("min-effect-dfeatures-browser", "step"),
    Output("min-effect-dfeatures-browser", "value"),
    Input("data-type-dfeatures-browser", "value"),
    prevent_initial_call=True,
)
def update_min_effect_slider(
    data_type: str,
) -> t.Tuple[bool, float, float, float, float]:
    """
    Function updates slider based on type of data Met or Exp.

    :param data_type:
    :return boolean, float, float, float, float:
    """
    if data_type == "Expression [RNA-seq]":
        return False, 1.0, 10.0, 1.0, 1.0
    if data_type == "Methylation [450K/EPIC]":
        return False, 0.05, 0.9, 0.05, 0.05

    return True, 0.0, 0.0, 0.0, 0.0


@callback(
    Output("download-dfeatures-frame", "data"),
    State("data-type-dfeatures-browser", "value"),
    State("groupA-dfeatures-browser", "value"),
    State("groupB-dfeatures-browser", "value"),
    State("alpha-dfeatures-browser", "value"),
    State("min-effect-dfeatures-browser", "value"),
    Input("download-dfeatures-button", "n_clicks"),
    prevent_initial_call=True,
)
def return_statistic_frame(
    data_type: str, group_A: str, group_B: str, alpha: float, effect: float, n_clicks: int
) -> pd.DataFrame:
    """
    Function sends frame with statistics to a user.

    :param data_type:
    :param group_A:
    :param group_B:
    :param alpha:
    :param effect:
    :param n_clicks:
    :return pd.DataFrame:
    """
    path = temp_file_path(data_type, group_A, group_B, alpha, effect)
    frame = pd.read_parquet(path)

    frame = frame.rename(
        columns={"-log10(p-value)": "negative log10(p-value)", "-log10(FDR)": "negative log10(FDR)"}
    )
    return dcc.send_data_frame(frame.to_csv, "summary_table.csv")


@app.long_callback(
    Output("plot-dfeatures-browser", "figure"),
    Output("cnt-plot-dfeatures-browser", "figure"),
    Output("result-section-dfeatures-browser", "is_open"),
    Output("msg-dfeatures-browser", "children"),
    Output("msg-section-dfeatures-browser", "is_open"),
    Output("progress-dfeatures-browser", "children"),
    Output("count-table-dfeatures-browser", "children"),
    State("data-type-dfeatures-browser", "value"),
    State("groupA-dfeatures-browser", "value"),
    State("groupB-dfeatures-browser", "value"),
    State("alpha-dfeatures-browser", "value"),
    State("min-effect-dfeatures-browser", "value"),
    Input("submit-dfeatures-browser", "n_clicks"),
    manager=long_callback_manager,
    prevent_initial_call=True,
)
def main_dfeatures_browser(
    data_type: str, group_A: str, group_B: str, alpha: float, effect_size: float, _: int
):
    """
    Function to perform DE/DM analysis.

    :param data_type:
    :param group_A:
    :param group_B:
    :param alpha:
    :param effect_size:
    :param _:
    :return Optional[Fig, boolean, str, boolean, str, pd.DataFrame]:
    """
    if data_type and group_A and group_B:

        if group_A == group_B:
            msg = f"Can not compare two identical groups of samples - '{group_A}' and '{group_B}'."
            send_slack_msg("Differential features browser", msg)
            return (
                EmptyFig,
                EmptyFig,
                False,
                msg,
                True,
                "",
                "",
            )

        loader = FrameOperations(data_type, [group_A, group_B])
        data, sample_frame = loader.load_mvf()

        diffF = DifferentialFeatures(
            data_type, data, sample_frame, group_A, group_B, alpha, effect_size
        )
        diffF.identify_differential_features()
        diffF.build_statistics_frame()

        path_to_drop = temp_file_path(data_type, group_A, group_B, alpha, effect_size)
        diffF.export(path_to_drop)
        results = diffF.stats_frame

        if data_type == "Expression [RNA-seq]":
            plot = Plot(results, "log2(FC)", "-log10(FDR)", None, None)
            fig = plot.volcanoplot(x_border=effect_size, y_border=-np.log10(alpha))
        else:
            plot = Plot(results, "delta", "-log10(FDR)", None, None)
            fig = plot.volcanoplot(x_border=effect_size, y_border=-np.log10(alpha))

        cnt_fig = plot.pieplot()
        count = Stats(sample_frame.to_frame(), "SampleType").get_factor_count

        log_info = f"Input: {data_type} - {group_A} - {group_B}"
        send_slack_msg("Differential features browser", log_info)
        logger.info(log_info)

        return fig, cnt_fig, True, "Status: done.", True, "", count

    return dash.no_update
