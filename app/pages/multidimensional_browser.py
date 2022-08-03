import typing as t

import dash

dash.register_page(__name__)

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback, callback_context, dcc, html
from src.basics import FrameOperations
from src.plots import MultiDimPlot
from src.statistics import Stats
from src.utils import load_config, response_multidim

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
                            id="data-type-multidim-explorer",
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
                        html.Label("Select sample type/s (max 5)"),
                        dcc.Dropdown(
                            id="sample-types-multidim-explorer",
                            options=[],
                            clearable=True,
                            multi=True,
                            disabled=True,
                        ),
                    ],
                    width=4,
                    style={"padding": "10px"},
                ),
                dbc.Col(
                    [
                        html.Label("Select number of dimensions"),
                        dcc.Slider(
                            id="n-dimension-multidim-explorer",
                            min=2,
                            max=3,
                            step=1,
                            value=2,
                        ),
                    ],
                    style={"padding": "10px"},
                ),
            ]
        ),
        dbc.Row(
            [
                html.Label("List of variables (max 100)"),
                html.Br(),
                dcc.Textarea(
                    id="input-multidim-explorer",
                    placeholder="Firstly select data type",
                    disabled=True,
                    style={
                        "width": "98%",
                        "margin-left": "10px",
                        "margin-bottom": "10px",
                    },
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label("Select scaling method"),
                        dcc.Dropdown(
                            id="scaling-method-multidim-explorer",
                            options=["None", "Log10", "Log2", "Ln", "Standard scaling"],
                            clearable=True,
                            multi=False,
                            value="Standard scaling",
                        ),
                    ],
                ),
                dbc.Col(
                    [
                        html.Label("Select decomposition method"),
                        dcc.Dropdown(
                            id="method-multidim-explorer",
                            options=["PCA", "t-SNE"],
                            value="PCA",
                            multi=False,
                            clearable=True,
                        ),
                    ]
                ),
                dbc.Col([html.Br(), dbc.Button("Submit", id="submit-multidim-explorer")]),
            ]
        ),
        dbc.Row(
            [dbc.Col(dbc.Spinner(html.Div(id="progress-multidim-explorer"), color="danger"))],
            style={"padding": "10px", "marginBottom": "10px", "marginTop": "10px"},
        ),
        dbc.Row(
            dbc.Collapse(
                [
                    dbc.Container(id="msg-multidim-explorer", fluid=True),
                    dcc.Graph(id="plot-multidim-explorer"),
                    dbc.Container(id="sample-count-multidim-explorer", fluid=True),
                ],
                id="result-section-multidim-explorer",
                is_open=False,
            ),
        ),
    ],
    fluid=True,
)


@callback(
    Output("sample-types-multidim-explorer", "options"),
    Output("sample-types-multidim-explorer", "disabled"),
    Input("data-type-multidim-explorer", "value"),
)
def update_sample_type_options(
    sample_types: t.Union[t.List[str], str]
) -> t.Tuple[t.List[str], bool]:
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

        return options, False
    else:
        return [], True


@callback(
    Output("input-multidim-explorer", "disabled"),
    Output("input-multidim-explorer", "placeholder"),
    Input("data-type-multidim-explorer", "value"),
)
def update_input_section(data_type):

    if data_type == "Expression [RNA-seq]":
        return False, "Eg. PAX3, PAX6, PARP9, AIM2, MX1"

    elif data_type == "Methylation [450K/EPIC]":
        return False, "Eg. cg07703401, cg03390211, cg15001381, cg16245339, cg25672287"

    else:
        return True, "Firstly select data type"


@callback(
    Output("plot-multidim-explorer", "figure"),
    Output("result-section-multidim-explorer", "is_open"),
    Output("msg-multidim-explorer", "children"),
    Output("progress-multidim-explorer", "children"),
    Output("sample-count-multidim-explorer", "children"),
    Input("sample-types-multidim-explorer", "value"),
    Input("data-type-multidim-explorer", "value"),
    Input("n-dimension-multidim-explorer", "value"),
    Input("input-multidim-explorer", "value"),
    Input("scaling-method-multidim-explorer", "value"),
    Input("method-multidim-explorer", "value"),
    Input("submit-multidim-explorer", "n_clicks"),
)
def update_figure(
    sample_types,
    data_type,
    n_dimensions,
    variables,
    scaling_method,
    method,
    submit_action,
):
    button = [p["prop_id"] for p in callback_context.triggered][0]

    if "submit-multidim-explorer" in button and sample_types and data_type and variables:
        variables = FrameOperations.clean_sequence(variables)

        if len(variables) < 5:
            return (
                emptyFig,
                True,
                "Less than 5 inputted variables. Instead use 1-D explorer",
                "",
                "",
            )

        if len(variables) > 100:
            return (
                emptyFig,
                True,
                "Exceeded maximum number of inputted variables [n > 100]",
                "",
                "",
            )

        if len(sample_types) > 5:
            return (
                emptyFig,
                True,
                "Exceeded maximum number of sample types [n > 5]",
                "",
                "",
            )

        loader = FrameOperations(data_type, sample_types)
        data = loader.load_many(variables)

        if data.empty:
            return emptyFig, True, "No common data in this set of sample types", "", ""

        if data.shape[1] - 1 < 5:
            return (
                emptyFig,
                True,
                "Found less than 5 variables in this set of sample types.",
                "",
                "",
            )

        data = loader.scale_many(data, scaling_method, "SampleType")
        stats = Stats(data, "SampleType")

        figureGenerator = MultiDimPlot(data, "SampleType", n_dimensions)

        if method == "t-SNE":
            fig = figureGenerator.tsne_plot()
        else:
            fig = figureGenerator.pca_plot()

        return fig, True, response_multidim(variables, data), "", stats.get_factor_count

    else:
        return emptyFig, False, "", "", ""
