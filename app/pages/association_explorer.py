import logging

import dash
import numpy as np

logger = logging.getLogger(__name__)
dash.register_page(__name__)

import dash_bootstrap_components as dbc
import dash_loading_spinners as dls
import pandas as pd
from dash import Input, Output, State, callback, dcc, html
from src.basics import FrameOperations
from src.plots import Plot
from src.regression import Model
from src.statistics import Stats
from src.utils import clean_gene_probe_id, load_config, send_slack_msg

EmptyFig = {}

config = load_config()
available_sample_types = pd.read_pickle(config["global_metadata"])
available_sample_types = available_sample_types[
    "Methylation_expression_files_with_common_samples_present"
]

layout = dbc.Container(
    [
        dbc.Row([html.Br(), html.H3("Methylation-expression explorer"), html.Hr()]),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label(
                            "Select sample category", htmlFor="sample-types-met-exp-browser"
                        ),
                        dcc.Dropdown(
                            id="sample-types-met-exp-browser",
                            options=available_sample_types,
                            clearable=True,
                            multi=False,
                            optionHeight=100,
                        ),
                    ],
                    xs=11,
                    sm=11,
                    md=4,
                    lg=4,
                    xl=4,
                ),
                dbc.Col(
                    [
                        html.Label(
                            "Gene name",
                            htmlFor="gene-met-exp-browser",
                            id="label-gene-1d-met-exp-browser",
                        ),
                        dbc.Input(
                            id="gene-met-exp-browser",
                            placeholder="Firstly select sample type",
                            disabled=True,
                            maxLength=10,
                            type="text",
                        ),
                    ],
                    xs=11,
                    sm=11,
                    md=4,
                    lg=4,
                    xl=4,
                ),
                dbc.Col(
                    [
                        html.Label(
                            "Probe ID",
                            htmlFor="probe-met-exp-browser",
                            id="label-probe-1d-met-exp-browser",
                            style={
                                "color": "blue",
                                "textDecoration": "underline",
                                "cursor": "pointer",
                            },
                        ),
                        dbc.Tooltip(
                            "Probe ID is a unique identifier from the appropriate [EPIC/450K] Illumina manifest.",
                            target="label-probe-1d-met-exp-browser",
                            placement="top",
                        ),
                        dbc.Input(
                            id="probe-met-exp-browser",
                            placeholder="Firstly select sample type",
                            disabled=True,
                            maxLength=10,
                            type="text",
                        ),
                    ],
                    xs=11,
                    sm=11,
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
                        html.Label(
                            "Degree of polynomial transformation",
                            htmlFor="poly-degree-met-exp-browser",
                        ),
                        dcc.Slider(
                            id="poly-degree-met-exp-browser",
                            min=1,
                            max=5,
                            step=1,
                            value=1,
                        ),
                        dbc.FormText("Affects only regression-based approach."),
                    ],
                    xs=12,
                    sm=12,
                    md=4,
                    lg=4,
                    xl=4,
                ),
                dbc.Col(
                    [
                        html.Label("Alpha (significance level)", htmlFor="alpha-met-exp-browser"),
                        dcc.Slider(
                            0.001,
                            0.1,
                            0.001,
                            value=0.05,
                            tooltip={"placement": "bottom", "always_visible": True},
                            marks=None,
                            id="alpha-met-exp-browser",
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
                        html.Label("Scaling method", htmlFor="scaling-method-met-exp-browser"),
                        dcc.Dropdown(
                            id="scaling-method-met-exp-browser",
                            options=["None", "Log10", "Log2", "Ln", "Standard scaling"],
                            clearable=True,
                            multi=False,
                            value="None",
                            placeholder="None (default)",
                        ),
                        dbc.FormText("Scaling method is applied only on dependent variable."),
                    ],
                    xs=12,
                    sm=12,
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
                        html.Label("Number of bins", htmlFor="n-bins-met-exp-browser"),
                        dcc.Dropdown(
                            id="n-bins-met-exp-browser",
                            options=[2, 3, 4],
                            clearable=True,
                            multi=False,
                            value=3,
                            placeholder="3 (default)",
                        ),
                        dbc.FormText("Affects only bins-based approach."),
                    ],
                    xs=12,
                    sm=12,
                    md=4,
                    lg=4,
                    xl=4,
                ),
                dbc.Col([html.Br(), dbc.Button("Submit", id="submit-met-exp-browser")]),
            ],
        ),
        html.Br(),
        dbc.Row(
            dbc.Col(
                dls.Hash(
                    html.Div(id="progress-met-exp-browser"),
                    color="#FF0000",
                    debounce=30,
                    speed_multiplier=2,
                    size=100,
                    fullscreen=True,
                    show_initially=False,
                )
            ),
        ),
        html.Br(),
        dbc.Row(
            dbc.Collapse(
                dbc.Card(
                    dbc.CardBody(html.P(id="msg-met-exp-browser", className="card-text")),
                    color="danger",
                    outline=True,
                ),
                id="msg-section-met-exp-browser",
            )
        ),
        html.Br(),
        dbc.Row(
            dbc.Collapse(
                [
                    dbc.Row(html.H5("Regression-based analysis")),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label(
                                        "Regression statistics", htmlFor="result-1-met-exp-browser"
                                    ),
                                    dbc.Container(id="result-1-met-exp-browser"),
                                ],
                                xs=12,
                                sm=12,
                                md=6,
                                lg=6,
                                xl=6,
                            ),
                            dbc.Col(
                                [
                                    html.Label(
                                        "Model parameters", htmlFor="result-2-met-exp-browser"
                                    ),
                                    dbc.Container(id="result-2-met-exp-browser"),
                                ],
                                xs=12,
                                sm=12,
                                md=6,
                                lg=6,
                                xl=6,
                            ),
                        ]
                    ),
                    dbc.Row(
                        dbc.Col(
                            dcc.Graph(
                                id="plot-met-exp-browser",
                                config={
                                    "toImageButtonOptions": {
                                        "format": "svg",
                                        "filename": "regression_based_plot.svg",
                                        "height": 500,
                                        "width": 700,
                                        "scale": 2,
                                    },
                                    "displayModeBar": True,
                                },
                            ),
                            xs=12,
                            sm=12,
                            md=12,
                            lg=12,
                            xl=12,
                        )
                    ),
                    dbc.Row(html.H5("Bin-based analysis")),
                    dbc.Row(
                        [
                            dbc.Col(
                                dcc.Graph(
                                    id="plot-2-met-exp-browser",
                                    config={
                                        "toImageButtonOptions": {
                                            "format": "svg",
                                            "filename": "bin_based_plot.svg",
                                            "height": 500,
                                            "width": 700,
                                            "scale": 2,
                                        },
                                        "displayModeBar": True,
                                    },
                                ),
                                xs=12,
                                sm=12,
                                md=12,
                                lg=12,
                                xl=12,
                            )
                        ]
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label(
                                        "Statistics frame",
                                        htmlFor="result-3-met-exp-browser",
                                    ),
                                    dbc.Container(id="result-3-met-exp-browser"),
                                ],
                                xs=12,
                                sm=12,
                                md=6,
                                lg=6,
                                xl=6,
                            ),
                            dbc.Col(
                                [
                                    html.Label(
                                        "Sample count frame", htmlFor="result-4-met-exp-browser"
                                    ),
                                    dbc.Container(id="result-4-met-exp-browser"),
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
                id="result-section-met-exp-browser",
                is_open=False,
            ),
        ),
        dbc.Row(style={"height": "15vh"}),
    ],
    fluid=True,
)


@callback(
    Output("gene-met-exp-browser", "disabled"),
    Output("gene-met-exp-browser", "placeholder"),
    Output("probe-met-exp-browser", "disabled"),
    Output("probe-met-exp-browser", "placeholder"),
    Input("sample-types-met-exp-browser", "value"),
    prevent_initial_call=True,
)
def update_inputs_fields(sample_type):
    """
    Function to update input fields [gene and cpg] based on selected sample type.

    :param sample_type:
    :return boolean, str, boolean, str:
    """
    if sample_type:
        return False, "E.g. CSNK1E", False, "E.g. cg01309213"

    return True, "Firstly select a sample type", True, "Firstly select a sample type"


@callback(
    Output("plot-met-exp-browser", "figure"),
    Output("plot-2-met-exp-browser", "figure"),
    Output("progress-met-exp-browser", "children"),
    Output("result-section-met-exp-browser", "is_open"),
    Output("result-1-met-exp-browser", "children"),
    Output("result-2-met-exp-browser", "children"),
    Output("result-3-met-exp-browser", "children"),
    Output("result-4-met-exp-browser", "children"),
    Output("msg-section-met-exp-browser", "is_open"),
    Output("msg-met-exp-browser", "children"),
    State("sample-types-met-exp-browser", "value"),
    State("gene-met-exp-browser", "value"),
    State("probe-met-exp-browser", "value"),
    State("poly-degree-met-exp-browser", "value"),
    State("alpha-met-exp-browser", "value"),
    State("scaling-method-met-exp-browser", "value"),
    State("n-bins-met-exp-browser", "value"),
    Input("submit-met-exp-browser", "n_clicks"),
    prevent_initial_call=True,
)
def update_model(sample_type, gene_id, probe_id, degree, alpha, scaling_method, n_bins, _: int):
    """
    Main function in association browser.

    :param sample_type:
    :param gene_id:
    :param probe_id:
    :param degree:
    :param alpha:
    :param scaling_method:
    :param n_bins:
    :param _:
    :return:
    """
    if sample_type and gene_id and probe_id:
        loader = FrameOperations("", sample_type)
        gene_id, probe_id = clean_gene_probe_id(
            gene_id, "Expression [RNA-seq]"
        ), clean_gene_probe_id(probe_id)
        frame, msg = loader.load_met_exp_frame(gene_id, probe_id)

        if frame.empty:
            send_slack_msg("Association browser", msg)
            logger.info(msg)
            return EmptyFig, EmptyFig, "", False, "", "", "", "", True, msg

        frame[gene_id] = loader.scale(frame[gene_id], scaling_method)

        model = Model(frame, gene_id, degree)
        model.prepare_data()

        model.fit_model()
        predicted = model.make_predictions()

        frame1, frame2 = model.export_frame()
        fig = model.plot(
            x_axis=probe_id, y_axis=gene_id, predicted=predicted, scaling_method=scaling_method
        )

        frame[probe_id] = FrameOperations.bin_variable(frame[probe_id], n_bins)

        stats = Stats(data=frame, factor=probe_id, alpha=alpha)
        stats.test_normality(gene_id)
        stats.test_normality(gene_id)
        stats.post_hoc(gene_id)

        frame3 = stats.export_frame()
        frame4 = stats.get_factor_count

        plots = Plot(
            frame,
            x_axis=probe_id,
            y_axis=gene_id,
            scaling_method=scaling_method,
            data_type="Expression",
            show_legend=False,
            show_x_ticks=True,
        )

        fig2 = plots.boxplot(order=np.sort(frame[probe_id].unique()).tolist())

        log_info = f"Input: {sample_type} - {gene_id} - {probe_id}"
        send_slack_msg("Association browser", log_info)
        logger.info(log_info)

        return fig, fig2, "", True, frame1, frame2, frame3, frame4, True, msg

    return dash.no_update
