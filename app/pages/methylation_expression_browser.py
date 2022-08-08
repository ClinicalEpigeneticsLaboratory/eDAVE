import dash

dash.register_page(__name__)

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, callback, dcc, html
from src.basics import FrameOperations
from src.regression import Model
from src.utils import load_config

EmptyFig = {}

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
                        html.Label("Select sample type", htmlFor="sample-types-met-exp-browser"),
                        dcc.Dropdown(
                            id="sample-types-met-exp-browser",
                            options=available_sample_types,
                            clearable=True,
                            multi=False,
                        ),
                    ],
                    width=4,
                ),
                dbc.Col(
                    [
                        html.Label("Input gene", htmlFor="gene-met-exp-browser"),
                        dbc.Input(
                            id="gene-met-exp-browser",
                            placeholder="Firstly select sample type",
                            disabled=True,
                            maxLength=10,
                            type="text",
                        ),
                    ],
                    width=4,
                ),
                dbc.Col(
                    [
                        html.Label("Input probe ID", htmlFor="probe-met-exp-browser"),
                        dbc.Input(
                            id="probe-met-exp-browser",
                            placeholder="Firstly select sample type",
                            disabled=True,
                            maxLength=10,
                            type="text",
                        ),
                    ],
                    width=4,
                ),
            ]
        ),
        dbc.Row(
            dbc.Col([html.Br(), dbc.Button("Submit", id="submit-met-exp-browser")]),
        ),
        dbc.Row(
            [dbc.Col(dbc.Spinner(html.Div(id="progress-met-exp-browser"), color="danger"))],
            style={"padding": "10px", "marginBottom": "10px", "marginTop": "10px"},
        ),
        dbc.Row(
            dbc.Collapse(
                dbc.Card(
                    dbc.CardBody(html.P(id="msg-met-exp-browser", className="card-text")),
                    color="danger",
                    outline=True,
                ),
                style={"bottomMargin": "10px"},
                id="msg-section-met-exp-browser",
            )
        ),
        dbc.Row(
            dbc.Collapse(
                dbc.Row(
                    [
                        dbc.Col([html.Br(), dbc.Container(id="result-met-exp-browser")]),
                        dbc.Col(
                            dcc.Graph(id="plot-met-exp-browser"),
                        ),
                    ]
                ),
                id="result-section-met-exp-browser",
                is_open=False,
            )
        ),
    ],
    fluid=True,
)


@callback(
    Output("gene-met-exp-browser", "disabled"),
    Output("gene-met-exp-browser", "placeholder"),
    Output("probe-met-exp-browser", "disabled"),
    Output("probe-met-exp-browser", "placeholder"),
    Input("sample-types-met-exp-browser", "value"),
)
def update_inputs_fields(sample_type):
    if sample_type:
        return False, "Eg. PODXL", False, "Eg. cg07703401"

    return True, "Firstly select sample type", True, "Firstly select sample type"


@callback(
    Output("plot-met-exp-browser", "figure"),
    Output("progress-met-exp-browser", "children"),
    Output("result-section-met-exp-browser", "is_open"),
    Output("result-met-exp-browser", "children"),
    Output("msg-section-met-exp-browser", "is_open"),
    Output("msg-met-exp-browser", "children"),
    State("sample-types-met-exp-browser", "value"),
    State("gene-met-exp-browser", "value"),
    State("probe-met-exp-browser", "value"),
    Input("submit-met-exp-browser", "n_clicks"),
)
def update_model(sample_type, gene_id, probe_id, n_clicks: int):

    if sample_type and gene_id and probe_id:
        loader = FrameOperations("", sample_type)
        frame, msg = loader.load_met_exp_frame(gene_id, probe_id)

        if frame.empty:
            return EmptyFig, "", False, "", True, msg

        model = Model(frame, gene_id)
        model.fit_model()
        frames = model.export_frame()

        fig = model.plot(x_axis=probe_id, y_axis=gene_id)

        return fig, "", True, frames, True, msg

    return EmptyFig, "", False, "", False, ""
