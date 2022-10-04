import typing as t

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler

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
        fig = px.box(data_frame=self.data, x=self.x_axis, y=self.y_axis, color=self.x_axis)
        fig.update_layout(
            showlegend=False,
            yaxis=dict(title=self.__yaxis_title()),
            xaxis=dict(title=""),
            font=dict(size=self.font_size),
        )

        return fig

    def violinplot(self) -> Figure:
        fig = px.violin(data_frame=self.data, x=self.x_axis, y=self.y_axis, color=self.x_axis)
        fig.update_layout(
            showlegend=False,
            yaxis=dict(title=self.__yaxis_title()),
            xaxis=dict(title=""),
            font=dict(size=self.font_size),
        )

        return fig


class MultiDimPlot:
    def __init__(
        self, data: pd.DataFrame, factor: str, n_dimension: int, perplexity: t.Optional[int]
    ):
        self.data = data
        self.factor = factor
        self.n_dimension = n_dimension
        self.perplexity = perplexity
        self.font_size = 14
        self.random_state = 101

    def tsne_plot(self) -> Figure:
        data_to_deco = self.data.drop(self.factor, axis=1)
        scaled_data_to_deco = StandardScaler().fit_transform(data_to_deco)

        tsne = TSNE(
            n_components=self.n_dimension,
            perplexity=self.perplexity,
            learning_rate="auto",
            n_iter=500,
            n_iter_without_progress=50,
            init="pca",
            random_state=self.random_state,
        )

        deco_data = tsne.fit_transform(scaled_data_to_deco)
        deco_data = pd.DataFrame(
            deco_data,
            index=data_to_deco.index,
            columns=[f"t-SNE {i}" for i in range(1, self.n_dimension + 1)],
        )

        deco_data = pd.concat((deco_data, self.data[self.factor]), axis=1)

        if self.n_dimension == 2:
            fig = px.scatter(deco_data, x="t-SNE 1", y="t-SNE 2", color=self.factor)
        else:
            fig = px.scatter_3d(deco_data, x="t-SNE 1", y="t-SNE 2", z="t-SNE 3", color=self.factor)

        fig.update_layout(font=dict(size=self.font_size))

        return fig

    def pca_plot(self) -> Figure:
        data_to_deco = self.data.drop(self.factor, axis=1)
        scaled_data_to_deco = StandardScaler().fit_transform(data_to_deco)

        pca = PCA(n_components=self.n_dimension, random_state=self.random_state)

        deco_data = pca.fit_transform(scaled_data_to_deco)
        exp = [round(val * 100, 2) for val in pca.explained_variance_ratio_]

        deco_data = pd.DataFrame(
            deco_data,
            index=data_to_deco.index,
            columns=[f"PC {i}" for i in range(1, self.n_dimension + 1)],
        )

        deco_data = pd.concat((deco_data, self.data[self.factor]), axis=1)
        names = deco_data.index
        names.name = "Case_ID"

        if self.n_dimension == 2:
            fig = px.scatter(
                deco_data,
                x="PC 1",
                y="PC 2",
                color=self.factor,
                hover_data=[names],
                labels={"PC 1": f"PC 1 {exp[0]}%", "PC 2": f"PC 2 {exp[1]}%"},
            )
        else:
            fig = px.scatter_3d(
                deco_data,
                x="PC 1",
                y="PC 2",
                z="PC 3",
                color=self.factor,
                hover_data=[names],
                labels={
                    "PC 1": f"PC 1 {exp[0]}%",
                    "PC 2": f"PC 2 {exp[1]}%",
                    "PC 3": f"PC 3 {exp[2]}%",
                },
            )

        fig.update_layout(font=dict(size=self.font_size))

        return fig
