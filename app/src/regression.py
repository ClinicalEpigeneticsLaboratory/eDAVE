import typing as t
from io import StringIO

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import statsmodels.api as sm
from dash import dash_table
from sklearn.preprocessing import PolynomialFeatures


class Model:
    def __init__(
        self, data: pd.DataFrame, response_variable: str, polynomial_degree: t.Optional[int]
    ):
        self.data = data
        self.response_variable = response_variable
        self.polynomial_degree = polynomial_degree
        self.model = None
        self.model_summary = None
        self.domain = None
        self.prepared_exog = None
        self.prepared_endo = None

    def prepare_data(self) -> None:
        """
        Method to prepare dataset before feed into regression model.
        Preparing process contains split original frame into exog and endo frames.
        Additionally polynomial transformation is applied here.

        :return None:
        """
        initial = self.data.drop(self.response_variable, axis=1)
        self.domain = (initial.min(), initial.max())

        self.prepared_endo = self.data[self.response_variable]

        if self.polynomial_degree > 1:
            name = initial.columns[0]
            transformed = PolynomialFeatures(
                degree=self.polynomial_degree, include_bias=False
            ).fit_transform(initial)
            transformed = pd.DataFrame(
                transformed,
                index=initial.index,
                columns=[f"{name}^{degree+1}" for degree in range(self.polynomial_degree)],
            )
            self.prepared_exog = transformed

        else:
            self.prepared_exog = initial

        self.prepared_exog.insert(0, "Intercept", 1)

    def fit_model(self) -> None:
        """
        Method to fit regression model.

        :return None:
        """
        model = sm.OLS(endog=self.prepared_endo, exog=self.prepared_exog)
        self.model = model.fit()
        self.model_summary = self.model.summary()

    def make_predictions(self) -> pd.DataFrame:
        """
        Method to generate set of predictions based on trained regression model.

        :return pd.DataFrame:
        """
        x_range = np.linspace(*self.domain, 100)

        if self.polynomial_degree > 1:
            transformed = PolynomialFeatures(
                degree=self.polynomial_degree, include_bias=False
            ).fit_transform(x_range)
            transformed = pd.DataFrame(transformed)
            to_predict = transformed

        else:
            to_predict = pd.DataFrame(x_range)

        to_predict.insert(0, "Intercept", 1)
        to_predict.columns = self.prepared_exog.columns

        predictions = self.model.predict(to_predict)
        predictions.index = x_range.flatten()

        return predictions

    def plot(
        self, x_axis: str, y_axis: str, predicted: pd.DataFrame, scaling_method: str
    ) -> go.Figure:
        """
        Method to generate plot with original set of data as well as trend line.

        :param x_axis:
        :param y_axis:
        :param predicted:
        :param scaling_method:
        :return Fig:
        """
        names = self.data.index
        names.name = "Case_ID"

        fig = px.scatter(
            data_frame=self.data,
            x=x_axis,
            y=y_axis,
            marginal_x="box",
            marginal_y="box",
            hover_data=[names],
            labels={
                x_axis: f"{x_axis} [β-value]",
                y_axis: f"{y_axis}: TPM, scaling: {scaling_method}",
            },
            opacity=0.85,
        )

        fig.add_traces(
            go.Scatter(
                x=predicted.index,
                y=predicted.values,
                name="Regression Fit",
                line={"color": "firebrick", "width": 3, "dash": "dot"},
            )
        )
        fig.update_layout(font={"size": 20})

        return fig

    def export_frame(self) -> t.Tuple[dash_table.DataTable, dash_table.DataTable]:
        """
        Method to convert frames from statsmodels model into dash tables.

        :return pd.DataFrame, pd.DataFrame:
        """
        table = self.model_summary.as_html()
        frames = pd.read_html(StringIO(table))
        frame1, frame2 = frames[0], frames[1]

        frame1 = dash_table.DataTable(
            data=frame1.to_dict("records"),
            columns=[{"name": "", "id": str(i)} for i in frame1.columns],
            style_table={
                "overflowX": "auto",
                "overflowY": "auto",
                "width": "100%",
                "minWidth": "100%",
                "maxWidth": "100%",
                "padding": "1%",
            },
            export_format="csv",
            virtualization=False,
            style_data={"whiteSpace": "normal", "height": "auto"},
        )

        frame2 = frame2.drop(0)
        frame2.columns = [
            "Parameter",
            "Coef",
            "Std err",
            "t",
            "p-value",
            "95%CI - lb",
            "95%CI - ub",
        ]
        frame2 = dash_table.DataTable(
            data=frame2.to_dict("records"),
            style_table={
                "overflowX": "auto",
                "overflowY": "auto",
                "width": "100%",
                "minWidth": "100%",
                "maxWidth": "100%",
                "padding": "1%",
            },
            export_format="csv",
            virtualization=False,
            style_data={"whiteSpace": "normal", "height": "auto"},
        )

        return frame1, frame2
