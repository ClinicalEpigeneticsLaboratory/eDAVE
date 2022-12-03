import numpy as np
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
        self.normality = None
        self.results = None

    def test_for_homoscedasticity(self, dependent_var: str) -> None:
        """
        Method to test for equal variance between analysed groups of samples.

        :param dependent_var:
        :return None:
        """
        records = [
            self.data.loc[ids, dependent_var].values
            for ids in self.data.groupby(self.factor).groups.values()
        ]
        _, pvalue = sts.levene(*records)

        if pvalue <= self.alpha:
            self.variance_equal = False
        else:
            self.variance_equal = True

    def test_normality(self, dependent_var: str) -> None:
        """
        Method to test for normality all analysed groups of samples.

        :param dependent_var:
        :return None:
        """
        records = [
            self.data.loc[ids, dependent_var].values
            for ids in self.data.groupby(self.factor).groups.values()
        ]
        stats = [sts.shapiro(record)[1] for record in records]
        stats = np.array(stats)

        if all(stats > self.alpha):
            self.normality = True
        else:
            self.normality = False

    def __tukey_test(self, dependent_var: str) -> pd.DataFrame:
        """
        Method to perform parametric (equal variance) post-hoc test.

        :param dependent_var:
        :return pd.DataFrame:
        """
        results = pg.pairwise_tukey(data=self.data, dv=dependent_var, between=self.factor)
        results = results.rename(columns={"p-tukey": "p-value"})
        results = results[["A", "B", "p-value"]]  # pylint: disable=unsubscriptable-object

        return results

    def __gameshowell(self, dependent_var: str) -> pd.DataFrame:
        """
        Method to perform parametric (unequal variance) post-hoc test.

        :param dependent_var:
        :return pd.DataFrame:
        """
        results = pg.pairwise_gameshowell(data=self.data, dv=dependent_var, between=self.factor)
        results = results.rename(columns={"pval": "p-value"})
        results = results[["A", "B", "p-value"]]  # pylint: disable=unsubscriptable-object

        return results

    def __pairwise_mnu(self, dependent_var: str) -> pd.DataFrame:
        """
        Method to perform non-parametric post-hoc test.

        :param dependent_var:
        :return pd.DataFrame:
        """
        results = pg.pairwise_tests(
            data=self.data,
            dv=dependent_var,
            between=self.factor,
            parametric=False,
            padjust="fdr_bh",
        )
        results = results.rename(columns={"p-unc": "p-value", "p-corr": "FDR"})

        if "FDR" in results.columns:
            return results[["A", "B", "p-value", "FDR"]]

        return results[["A", "B", "p-value"]]

    def __annotate_posthoc_frame(self, results: pd.DataFrame, dependent_var: str) -> pd.DataFrame:
        """
        Method to annotate results from post-hoc tests.

        :param results:
        :param dependent_var:
        :return pd.DataFrame:
        """
        average = self.data.groupby(self.factor).mean()

        a_average = average.rename(columns={dependent_var: "mean(A)"})
        b_average = average.rename(columns={dependent_var: "mean(B)"})

        results = pd.merge(results, a_average, how="inner", left_on="A", right_index=True)
        results = pd.merge(results, b_average, how="inner", left_on="B", right_index=True)

        return results

    def __effect_size(self, results: pd.DataFrame, dependent_var: str) -> pd.DataFrame:
        """
        Method to calculate effect size.
        Effect size expressed as: fold-change (FC), Delta and Hedges` g.

        :param results:
        :param dependent_var:
        :return pd.DataFrame:
        """
        results_extended = results.copy()

        for index, record in results_extended.iterrows():

            group_a, group_b = record["A"], record["B"]
            var_a = self.data[self.data[self.factor] == group_a][dependent_var]
            var_b = self.data[self.data[self.factor] == group_b][dependent_var]

            effect = pg.compute_effsize(var_a, var_b, paired=False, eftype="hedges")
            fc = var_a.mean() / var_b.mean()
            delta = var_a.mean() - var_b.mean()

            results_extended.loc[index, "Hedges` g"] = effect
            results_extended.loc[index, "FC"] = fc
            results_extended.loc[index, "delta"] = delta

        return results_extended.round(3)

    def post_hoc(self, dependent_var: str) -> None:
        """
        Method to apply appropriate post-hoc test based on results from normality and homoscedasticity tests.

        :param dependent_var:
        :return None:
        """
        if self.variance_equal and self.normality:
            results = self.__tukey_test(dependent_var)
            test = "parametric"

        elif not self.variance_equal and self.normality:
            results = self.__gameshowell(dependent_var)
            test = "parametric - not equal variance"

        else:
            results = self.__pairwise_mnu(dependent_var)
            test = "non-parametric"

        results = self.__annotate_posthoc_frame(results, dependent_var)
        results = self.__effect_size(results, dependent_var)
        results["Type"] = test

        self.results = results

    def export_frame(self) -> dash_table:
        """
        Method to convert data frame containing statistics to dash data table object.

        :return dash_table:
        """
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
        """
        Method returns dash table containing counts of samples per types.

        :return dash_table:
        """
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

    def find_optimal_cluster_number(self) -> pd.Series:
        """
        Method to identify optimal number of clusters within specific multidimensional dataset.
        The point of this implementation is to find n_clusters maximising calinski harabasz metric.

        :return pd.Series:
        """
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
