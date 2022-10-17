from io import StringIO

import pandas as pd
from dash import dash_table
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import calinski_harabasz_score
from statsmodels.stats.multicomp import pairwise_tukeyhsd


class Stats:
    def __init__(self, data: pd.DataFrame, factor: str, alpha: float = 0.05):
        self.data = data
        self.factor = factor
        self.alpha = alpha
        self.results = None

    def post_hoc(self) -> None:
        posthoc = pairwise_tukeyhsd(
            endog=self.data.drop(self.factor, axis=1),
            groups=self.data[self.factor],
            alpha=self.alpha,
        )
        self.results = posthoc.summary()

    def export_frame(self) -> dash_table:
        html = self.results.as_html()
        frame = pd.read_html(StringIO(html))[0]
        frame = frame.to_dict("records")

        frame = dash_table.DataTable(
            frame,
            style_table={
                "overflowX": "auto",
                "overflowY": "auto",
                "width": "100%",
                "minWidth": "100%",
                "maxWidth": "100%",
            },
            style_data={"whiteSpace": "normal", "height": "auto"},
        )
        return frame

    @property
    def get_factor_count(self) -> dash_table:
        cnt = self.data[self.factor].value_counts().to_frame().reset_index()
        cnt.columns = ["Sample type", "Count"]
        cnt = cnt.to_dict("records")
        cnt = dash_table.DataTable(
            cnt,
            style_table={
                "overflowX": "auto",
                "overflowY": "auto",
                "width": "100%",
                "minWidth": "100%",
                "maxWidth": "100%",
            },
            style_data={"whiteSpace": "normal", "height": "auto"},
        )

        return cnt


class ClusterAnalysis:
    def __init__(self, data: pd.DataFrame, factor: str):
        self.data = data
        self.factor = factor

    def find_optimal_cluster_number(self):
        data = self.data.drop(self.factor, axis=1)
        results = {}
        max_number_of_clusters = self.data[self.factor].nunique() * 2 + 1

        for n in range(2, max_number_of_clusters):
            clustering = AgglomerativeClustering(n_clusters=n, linkage="ward")
            clustering.fit(data)
            labels = clustering.labels_

            scoring = calinski_harabasz_score(data, labels)
            results[n] = scoring

        optimal_number_of_clusters = max(results, key=results.get)
        clustering = AgglomerativeClustering(n_clusters=optimal_number_of_clusters, linkage="ward")
        clustering.fit(data)
        optimal_labels = clustering.labels_

        optimal_labels = [f"Cluster {n}" for n in optimal_labels]
        optimal_labels = pd.Series(optimal_labels, index=data.index, name="SampleType")

        return optimal_labels
