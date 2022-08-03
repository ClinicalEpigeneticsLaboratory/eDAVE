import dash

dash.register_page(__name__)

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback, callback_context, dcc, html
from src.basics import FrameOperations
from src.regression import Model
from src.utils import load_config

emptyFig = go.Figure()

config = load_config()
available_sample_types = pd.read_pickle(config["global_metadata"])
available_sample_types = available_sample_types[
    "Methylation_expression_files_with_common_samples_present"
]

layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label("Select sample type"),
                        dcc.Dropdown(
                            id="sample-types-met-exp-explorer",
                            options=available_sample_types,
                            clearable=True,
                            multi=False,
                        ),
                    ],
                    width=4,
                    style={"padding": "10px"},
                ),
                dbc.Col(
                    [
                        html.Label("Input gene"),
                        dbc.Input(
                            id="gene-met-exp-explorer",
                            placeholder="Firstly select sample type",
                            disabled=True,
                            maxLength=10,
                            type="text",
                        ),
                    ],
                    width=4,
                    style={"padding": "10px"},
                ),
                dbc.Col(
                    [
                        html.Label("Input probe ID"),
                        dbc.Input(
                            id="probe-met-exp-explorer",
                            placeholder="Firstly select sample type",
                            disabled=True,
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
            dbc.Col([html.Br(), dbc.Button("Submit", id="submit-met-exp-explorer")]),
        ),
        dbc.Row(
            [dbc.Col(dbc.Spinner(html.Div(id="progress-met-exp-explorer"), color="danger"))],
            style={"padding": "10px", "marginBottom": "10px", "marginTop": "10px"},
        ),
        dbc.Row(
            dbc.Collapse(
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Container(id="result-met-exp-explorer"),
                        ),
                        dbc.Col(
                            dcc.Graph(id="plot-met-exp-explorer"),
                        ),
                    ]
                ),
                id="result-section-met-exp-explorer",
                is_open=False,
            )
        ),
    ],
    fluid=True,
)


@callback(
    Output("gene-met-exp-explorer", "disabled"),
    Output("gene-met-exp-explorer", "placeholder"),
    Output("probe-met-exp-explorer", "disabled"),
    Output("probe-met-exp-explorer", "placeholder"),
    Input("sample-types-met-exp-explorer", "value"),
)
def update_inputs_fields(sample_type):
    if sample_type:
        return False, "Eg. PODXL", False, "Eg. cg07703401"
    else:
        return True, "Firstly select sample type", True, "Firstly select sample type"


@callback(
    Output("plot-met-exp-explorer", "figure"),
    Output("progress-met-exp-explorer", "children"),
    Output("result-section-met-exp-explorer", "is_open"),
    Output("result-met-exp-explorer", "children"),
    Input("sample-types-met-exp-explorer", "value"),
    Input("gene-met-exp-explorer", "value"),
    Input("probe-met-exp-explorer", "value"),
    Input("submit-met-exp-explorer", "n_clicks"),
)
def update_model(sample_type, gene_id, probe_id, submit_action):
    button = [p["prop_id"] for p in callback_context.triggered][0]

    if "submit-met-exp-explorer" in button and sample_type and gene_id and probe_id:
        loader = FrameOperations("", sample_type)
        interrupt, frame = loader.load_met_exp_frame(gene_id, probe_id)

        if interrupt:
            return emptyFig, "", True, frame

        model = Model(frame, gene_id)
        model.fit_model()

        fig = model.plot(x_axis=probe_id, y_axis=gene_id)

        return fig, "", True, model.export_frame()

    else:
        return emptyFig, "", False, ""
