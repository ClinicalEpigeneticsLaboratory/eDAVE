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
        self.names = self.data.index
        self.names.name = "Case_ID"

        self.x_axis = x_axis
        self.y_axis = y_axis
        self.scaling_method = scaling_method
        self.data_type = data_type
        self.font_size = font_size

    def __yaxis_title(self) -> str:
        """
        Method to set y axis title.
        :return str:
        """
        if self.data_type == "Methylation [450K/EPIC]":
            return f"units: β-value, scaling: {self.scaling_method}"

        return f"units: TPM, scaling: {self.scaling_method}"

    def boxplot(self) -> Figure:
        """
        Method to generate boxplot.

        :return Fig:
        """
        fig = px.box(
            data_frame=self.data,
            x=self.x_axis,
            y=self.y_axis,
            color=self.x_axis,
            hover_data=[self.names],
        )
        fig.update_layout(
            yaxis=dict(title=self.__yaxis_title()),
            xaxis=dict(title="", showticklabels=False),
            font=dict(size=self.font_size),
            legend=dict(title="", orientation="h", y=-0.2),
        )

        return fig

    def violinplot(self) -> Figure:
        """
        Method to generate violinplot.

        :return Fig:
        """
        fig = px.violin(
            data_frame=self.data,
            x=self.x_axis,
            y=self.y_axis,
            color=self.x_axis,
            hover_data=[self.names],
        )
        fig.update_layout(
            yaxis=dict(title=self.__yaxis_title()),
            xaxis=dict(title="", showticklabels=False),
            font=dict(size=self.font_size),
            legend=dict(title="", orientation="h", y=-0.2),
        )

        return fig

    def scatterplot(self) -> Figure:
        """
        Method to generate scatterplot.

        :return Fig:
        """
        fig = px.strip(
            data_frame=self.data,
            x=self.x_axis,
            y=self.y_axis,
            color=self.x_axis,
            hover_data=[self.names],
        )
        fig.update_layout(
            yaxis=dict(title=self.__yaxis_title()),
            xaxis=dict(title="", showticklabels=False),
            font=dict(size=self.font_size),
            legend=dict(title="", orientation="h", y=-0.2),
        )

        return fig

    def volcanoplot(self, x_border: float, y_border: float) -> Figure:
        """
        Method to generate volcanoplot.

        :return Fig:
        """
        names = self.data.index
        names.name = "Feature"

        fig = px.scatter(
            data_frame=self.data,
            x=self.x_axis,
            y=self.y_axis,
            hover_data=[names, self.data.FC, self.data.delta, self.data["Hedge`s g"]],
            color="DEG/DMP",
            color_discrete_map={True: "red", False: "blue"},
        )

        fig.update_layout(font=dict(size=self.font_size))

        fig.add_hline(y=y_border, line_dash="dash", line_color="gray")
        fig.add_vline(x=-x_border, line_dash="dash", line_color="gray")
        fig.add_vline(x=x_border, line_dash="dash", line_color="gray")

        return fig


class MultiDimPlot:
    def __init__(self, data: pd.DataFrame, factor: str, n_dimensions: int):
        self.data = data
        self.factor = factor
        self.n_dimensions = n_dimensions
        self.font_size = 14

    def plot(self) -> Figure:
        """
        Method to generate scatterplot for 2 and 3 dimensional datasets.

        :return Fig:
        """
        data = self.data.copy()
        names = data.index
        names.name = "Case_ID"

        if self.n_dimensions == 2:
            col1, col2 = data.columns[0], data.columns[1]
            fig = px.scatter(
                data,
                x=col1,
                y=col2,
                color=self.factor,
                hover_data=[names],
                category_orders={self.factor: sorted(self.data[self.factor].unique())},
            )
        else:
            col1, col2, col3 = data.columns[0], data.columns[1], data.columns[2]
            fig = px.scatter_3d(
                data,
                x=col1,
                y=col2,
                z=col3,
                color=self.factor,
                hover_data=[names],
                category_orders={self.factor: sorted(self.data[self.factor].unique())},
            )
            fig.update_layout(
                margin=dict(l=0, r=0, t=0, b=0), scene_camera=dict(eye=dict(x=2.0, y=2.0, z=0.75))
            )

        fig.update_layout(
            font=dict(size=self.font_size),
            legend=dict(title="", orientation="h", y=-0.2),
        )

        return fig
