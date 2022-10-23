import logging
import typing as t

import dash

logger = logging.getLogger(__name__)
dash.register_page(__name__)

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, callback, dcc, html
from src.basics import FrameOperations
from src.decomposition import DataDecomposition
from src.plots import MultiDimPlot
from src.statistics import ClusterAnalysis, Stats
from src.utils import load_config, response_multidim

EmptyFig = {}
config = load_config()
global_metadata = pd.read_pickle(config["global_metadata"])

layout = dbc.Container(
    [
        dbc.Row([html.Br(), html.H3("Multidimensional browser"), html.Hr()]),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label("Data type", htmlFor="data-type-multidim-browser"),
                        dcc.Dropdown(
                            id="data-type-multidim-browser",
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
                        html.Label("Select sample type/s", htmlFor="sample-types-multidim-browser"),
                        dcc.Dropdown(
                            id="sample-types-multidim-browser",
                            options=[],
                            placeholder="Firstly select a data type",
                            clearable=True,
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
                            "Select number of dimensions", htmlFor="n-dimension-multidim-browser"
                        ),
                        dcc.Slider(
                            id="n-dimension-multidim-browser",
                            min=2,
                            max=3,
                            step=1,
                            value=2,
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
                html.Label(
                    "List of variables [probes IDs/genes]",
                    htmlFor="input-multidim-browser",
                ),
                dcc.Textarea(
                    id="input-multidim-browser",
                    placeholder="Firstly select a data type",
                    disabled=True,
                    style={"width": "98%"},
                ),
                dbc.FormText("Number of input variables must be >= 10 and <= 100"),
            ],
            justify="center",
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label(
                            "Select decomposition method", htmlFor="method-multidim-browser"
                        ),
                        dcc.Dropdown(
                            id="method-multidim-browser",
                            options=["PCA", "t-SNE"],
                            value="PCA",
                            clearable=True,
                        ),
                    ],
                    xs=10,
                    sm=10,
                    md=5,
                    lg=5,
                    xl=5,
                ),
                dbc.Col(
                    [
                        html.Label("Perplexity", htmlFor="perplexity-multidim-browser"),
                        dcc.Slider(
                            min=1,
                            max=10,
                            step=1,
                            value=5,
                            disabled=True,
                            id="perplexity-multidim-browser",
                        ),
                        dbc.FormText("Parameter available only for t-SNE method"),
                    ],
                    xs=10,
                    sm=10,
                    md=5,
                    lg=5,
                    xl=5,
                ),
                dbc.Col(dbc.Button("Submit", id="submit-multidim-browser")),
            ]
        ),
        html.Br(),
        dbc.Row(
            dbc.Col(dbc.Spinner(html.Div(id="progress-multidim-browser"), color="danger")),
        ),
        html.Br(),
        dbc.Row(
            dbc.Collapse(
                dbc.Card(
                    dbc.CardBody(html.P(id="msg-multidim-browser", className="card-text")),
                    color="danger",
                    outline=True,
                ),
                id="msg-section-multidim-browser",
            )
        ),
        html.Br(),
        dbc.Row(
            dbc.Collapse(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label(
                                        "Samples marked by type", htmlFor="plot-multidim-browser"
                                    ),
                                    dcc.Graph(id="plot-multidim-browser"),
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
                                        "Samples marked by predicted cluster",
                                        htmlFor="plot-2-multidim-browser",
                                    ),
                                    dcc.Graph(id="plot-2-multidim-browser"),
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
                        [
                            html.Label("Sample count", htmlFor="sample-count-multidim-browser"),
                            dbc.Container(id="sample-count-multidim-browser", fluid=True),
                        ]
                    ),
                ],
                id="result-section-multidim-browser",
                is_open=False,
            ),
        ),
        dbc.Row(style={"height": "15vh"}),
    ],
    fluid=True,
)


@callback(
    Output("sample-types-multidim-browser", "options"),
    Output("sample-types-multidim-browser", "disabled"),
    Output("sample-types-multidim-browser", "value"),
    Input("data-type-multidim-browser", "value"),
)
def update_sample_type_options(
    data_type: t.Union[t.List[str], str]
) -> t.Tuple[t.List[str], bool, str]:
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

        return options, False, ""

    return [], True, ""


@callback(
    Output("input-multidim-browser", "disabled"),
    Output("input-multidim-browser", "value"),
    Input("data-type-multidim-browser", "value"),
)
def update_input_section(data_type):
    if data_type == "Expression [RNA-seq]":
        genes = (
            "Example input (genes names are case sensitive) --> PAX3, SOX8, PARP9, AIM2, "
            "MX1, TSPAN6, DPM1, SCYL3, NIPAL3, LAS1L"
        )
        return False, genes

    if data_type == "Methylation [450K/EPIC]":
        cpgs = (
            "Example input --> cg10009236, cg08203127, cg26912541, cg08823186, "
            "cg26616258, cg01546397, cg03884976, cg26804023, "
            "cg07843956, cg00469995"
        )
        return False, cpgs

    return True, "Firstly select a data type"


@callback(
    Output("perplexity-multidim-browser", "disabled"), Input("method-multidim-browser", "value")
)
def update_slider(method: str):
    if method == "t-SNE":
        return False

    return True


@callback(
    Output("plot-multidim-browser", "figure"),
    Output("plot-2-multidim-browser", "figure"),
    Output("result-section-multidim-browser", "is_open"),
    Output("msg-multidim-browser", "children"),
    Output("msg-section-multidim-browser", "is_open"),
    Output("progress-multidim-browser", "children"),
    Output("sample-count-multidim-browser", "children"),
    State("data-type-multidim-browser", "value"),
    State("sample-types-multidim-browser", "value"),
    State("n-dimension-multidim-browser", "value"),
    State("input-multidim-browser", "value"),
    State("perplexity-multidim-browser", "value"),
    State("method-multidim-browser", "value"),
    Input("submit-multidim-browser", "n_clicks"),
)
def main_multidim_browser(
    data_type: str,
    sample_types: list,
    n_dimensions: int,
    variables: str,
    perplexity: int,
    method: str,
    n_clicks: int,
):
    if sample_types and data_type and variables:
        variables = FrameOperations.clean_sequence(variables)

        if len(variables) < 10:
            logger.info("Aborted: len(variables) < 10")
            return EmptyFig, EmptyFig, False, "Less than 10 inputted variables.", True, "", ""

        if len(variables) > 100:
            logger.info("Aborted: len(variables) > 100")
            return (
                EmptyFig,
                EmptyFig,
                False,
                "Exceeded maximum number of inputted variables [n > 100].",
                True,
                "",
                "",
            )

        if len(sample_types) > 5:
            logger.info("Aborted: len(sample_types) > 5")
            return (
                EmptyFig,
                EmptyFig,
                False,
                "Exceeded maximum number of sample types [n > 5].",
                True,
                "",
                "",
            )

        loader = FrameOperations(data_type, sample_types)
        data = loader.load_many(variables)
        count = Stats(data, "SampleType").get_factor_count

        if data.empty:
            logger.info("Aborted: no common data in this set of sample types.")
            return (
                EmptyFig,
                EmptyFig,
                False,
                "No common data in this set of sample types.",
                True,
                "",
                "",
            )

        if data.shape[1] - 1 < 5:
            logger.info("Aborted: less than 5 variables.")
            return (
                EmptyFig,
                EmptyFig,
                False,
                "Identified less than 5 variables in this set of sample types.",
                True,
                "",
                "",
            )

        transformer = DataDecomposition(data, "SampleType", n_dimensions)

        if method == "t-SNE":
            deco_data = transformer.tsne(perplexity=perplexity)
        else:
            deco_data = transformer.pca()

        plot_generator = MultiDimPlot(deco_data, "SampleType", n_dimensions)
        fig_1 = plot_generator.plot()

        cls = ClusterAnalysis(deco_data, "SampleType")
        optimal_labels = cls.find_optimal_cluster_number()

        deco_data["SampleType"] = optimal_labels
        plot_generator = MultiDimPlot(deco_data, "SampleType", n_dimensions)
        fig_2 = plot_generator.plot()

        logger.info(
            f"Input: {sample_types} - {data_type} - {variables} - {method} - {n_dimensions}"
        )
        return fig_1, fig_2, True, response_multidim(variables, data), True, "", count

    return dash.no_update
