from io import StringIO

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import statsmodels.api as sm
from dash import dash_table


class Model:
    def __init__(self, data: pd.DataFrame, response_variable: str):
        self.data = data
        self.data["intercept"] = 1
        self.response_variable = response_variable
        self.model_summary = None
        self.predictions = None

    def fit_model(self):
        model = sm.OLS(
            endog=self.data[self.response_variable],
            exog=self.data.drop(self.response_variable, axis=1),
        )

        model = model.fit()
        self.model_summary = model.summary()
        self.predictions = model.predict(self.data.drop(self.response_variable, axis=1))

    def plot(self, x_axis: str, y_axis: str) -> go.Figure:
        fig = px.scatter(
            data_frame=self.data,
            x=x_axis,
            y=y_axis,
            marginal_x="box",
            marginal_y="box",
            trendline="ols",
        )
        fig.update_layout(font=dict(size=14))

        return fig

    def export_frame(self) -> dash_table:
        html = self.model_summary.as_html()
        frames = pd.read_html(StringIO(html))
        frame1, frame2 = frames[0], frames[1]

        frame1 = dash_table.DataTable(
            data=frame1.to_dict("records"),
            columns=[{"name": "", "id": str(i)} for i in frame1.columns],
        )
        frame2 = dash_table.DataTable(
            data=frame2.to_dict("records"),
            columns=[{"name": "", "id": str(i)} for i in frame2.columns],
        )

        return frame1, frame2
