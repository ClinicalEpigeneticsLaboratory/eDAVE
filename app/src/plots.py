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
            data_frame=self.data,
            x=self.x_axis,
            y=self.y_axis,
            color=self.x_axis,
        )
        fig.update_layout(
            yaxis=dict(title=self.__yaxis_title()),
            xaxis=dict(title="", showticklabels=False),
            font=dict(size=self.font_size),
            legend=dict(title="", orientation="h", y=-0.2),
        )

        return fig

    def violinplot(self) -> Figure:
        fig = px.violin(
            data_frame=self.data,
            x=self.x_axis,
            y=self.y_axis,
            color=self.x_axis,
        )
        fig.update_layout(
            yaxis=dict(title=self.__yaxis_title()),
            xaxis=dict(title="", showticklabels=False),
            font=dict(size=self.font_size),
            legend=dict(title="", orientation="h", y=-0.2),
        )

        return fig

    def scatterplot(self) -> Figure:
        fig = px.strip(
            data_frame=self.data,
            x=self.x_axis,
            y=self.y_axis,
            color=self.x_axis,
        )
        fig.update_layout(
            yaxis=dict(title=self.__yaxis_title()),
            xaxis=dict(title="", showticklabels=False),
            font=dict(size=self.font_size),
            legend=dict(title="", orientation="h", y=-0.2),
        )

        return fig

    def volcanoplot(self, x_border: float, y_border: float) -> Figure:
        fig = px.scatter(
            data_frame=self.data, x=self.x_axis, y=self.y_axis, hover_data=[self.data.index]
        )

        fig.update_layout(
            yaxis=dict(title="-log10(p-value)"),
            xaxis=dict(title="log2(FC)"),
            font=dict(size=self.font_size),
            legend=dict(title="", orientation="h", y=-0.2),
        )

        fig.add_hline(y=y_border, line_dash="dash", line_color="red")
        fig.add_vline(x=-x_border, line_dash="dash", line_color="red")
        fig.add_vline(x=x_border, line_dash="dash", line_color="red")

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
