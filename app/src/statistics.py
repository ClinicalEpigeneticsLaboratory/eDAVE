import pandas as pd
import pingouin as pg
import scipy.stats as sts
from dash import dash_table
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import calinski_harabasz_score


class Stats:
    def __init__(self, data: pd.DataFrame, factor: str, alpha: float = 0.05):
        self.data = data
        self.factor = factor
        self.alpha = alpha
        self.variance_equal = None
        self.results = None

    def test_for_variance_heterogeneity(self, dependent_var: str) -> None:
        records = [
            self.data.loc[ids, dependent_var].values
            for ids in self.data.groupby(self.factor).groups.values()
        ]
        _, pvalue = sts.levene(*records)

        if pvalue <= self.alpha:
            self.variance_equal = False
        else:
            self.variance_equal = True

    def __add_status(self, pvalue: float) -> bool:
        if pvalue <= self.alpha:
            return True
        return False

    def post_hoc(self, dependent_var: str) -> None:
        if self.variance_equal:
            results = pg.pairwise_tukey(
                data=self.data, dv=dependent_var, between=self.factor, effsize="cohen"
            )
            results = results.rename(columns={"p-tukey": "pvalue"})
            test = "pairwise_tukey"

        else:
            results = pg.pairwise_gameshowell(
                data=self.data, dv=dependent_var, between=self.factor, effsize="cohen"
            )
            results = results.rename(columns={"pval": "pvalue"})
            test = "pairwise_gameshowell"

        results["FC"] = results["mean(A)"] / results["mean(B)"]
        results["H0 reject"] = results["pvalue"].map(self.__add_status)
        results = results.round(4)
        results["test"] = test

        self.results = results

    def export_frame(self) -> dash_table:
        frame = self.results.to_dict("records")
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
