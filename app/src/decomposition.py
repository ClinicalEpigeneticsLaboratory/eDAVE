import typing as t

import pandas as pd
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler


class DataDecomposition:
    def __init__(self, data: pd.DataFrame, factor: str, n_components: int):
        self.data = data
        self.factor = factor
        self.n_components = n_components
        self.random_state = 101

    def __prepare_data(self) -> t.Tuple[pd.DataFrame, pd.Series]:
        """
        Method to scale inputted dataset.

        :return pd.DataFrame, pd.Series:
        """
        data = self.data.drop(self.factor, axis=1)
        transformer = StandardScaler()
        scaled_data = transformer.fit_transform(data)

        return (
            pd.DataFrame(scaled_data, columns=data.columns, index=data.index),
            self.data[self.factor],
        )

    def tsne(
        self,
        perplexity: int,
        n_iter: int = 1000,
        n_iter_without_progress: int = 100,
        init: str = "pca",
    ) -> pd.DataFrame:
        """
        Method to apply t-SNE.

        :param perplexity:
        :param n_iter:
        :param n_iter_without_progress:
        :param init:
        :return pd.DataFrame:
        """
        tsne = TSNE(
            n_components=self.n_components,
            random_state=self.random_state,
            perplexity=perplexity,
            n_iter=n_iter,
            n_iter_without_progress=n_iter_without_progress,
            init=init,
        )

        data_to_deco, factor = self.__prepare_data()
        deco_data = tsne.fit_transform(data_to_deco)

        col_names = [f"t-SNE{i}" for i in range(1, self.n_components + 1)]
        deco_data = pd.DataFrame(deco_data, index=data_to_deco.index, columns=col_names)

        return pd.concat((deco_data, factor), axis=1)

    def pca(self) -> pd.DataFrame:
        """
        Method to apply PCA.

        :return pd.DataFrame:
        """
        pca = PCA(n_components=self.n_components, random_state=self.random_state)
        data_to_deco, factor = self.__prepare_data()
        deco_data = pca.fit_transform(data_to_deco)

        col_names = [
            f"PCA{cnt + 1} {round(var * 100, 0)}%"
            for cnt, var in enumerate(pca.explained_variance_ratio_)
        ]
        deco_data = pd.DataFrame(deco_data, index=data_to_deco.index, columns=col_names)

        return pd.concat((deco_data, factor), axis=1)
