import typing as t

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

Figure = go.Figure


class Plot:
    def __init__(
        self,
        data: pd.DataFrame,
        x_axis: str,
        y_axis: str,
        scaling_method: str,
        data_type: str,
        font_size: int = 14,
    ):
        self.data = data
        self.x_axis = x_axis
        self.y_axis = y_axis
        self.scaling_method = scaling_method
        self.data_type = data_type
        self.font_size = font_size

    def __yaxis_title(self) -> str:
        if self.data_type == "Methylation [450K/EPIC]":
            return f"units: β-value, scaling: {self.scaling_method}"

        return f"units: TPM, scaling: {self.scaling_method}"

    def boxplot(self) -> Figure:
        fig = px.box(
            data_frame=self.data, x=self.x_axis, y=self.y_axis, color=self.x_axis, points="all"
        )
        fig.update_layout(
            yaxis=dict(title=self.__yaxis_title()),
            xaxis=dict(title="", showticklabels=False),
            font=dict(size=self.font_size),
            legend=dict(title="Sample type", orientation="h"),
        )

        return fig

    def violinplot(self) -> Figure:
        fig = px.violin(
            data_frame=self.data, x=self.x_axis, y=self.y_axis, color=self.x_axis, points="all"
        )
        fig.update_layout(
            yaxis=dict(title=self.__yaxis_title()),
            xaxis=dict(title="", showticklabels=False),
            font=dict(size=self.font_size),
            legend=dict(title="Sample type", orientation="h"),
        )

        return fig


class MultiDimPlot:
    def __init__(self, data: pd.DataFrame, factor: str, n_dimensions: int):
        self.data = data
        self.factor = factor
        self.n_dimensions = n_dimensions
        self.font_size = 14

    def plot(self) -> Figure:
        data = self.data.copy()
        names = data.index
        names.name = "Case_ID"

        if self.n_dimensions == 2:
            col1, col2 = data.columns[0], data.columns[1]
            fig = px.scatter(data, x=col1, y=col2, color=self.factor, hover_data=[names])
        else:
            col1, col2, col3 = data.columns[0], data.columns[1], data.columns[2]
            fig = px.scatter_3d(data, x=col1, y=col2, z=col3, color=self.factor, hover_data=[names])

        fig.update_layout(
            font=dict(size=self.font_size), legend=dict(title="Sample type", orientation="h")
        )

        return fig
