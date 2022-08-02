from io import StringIO
import pandas as pd
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from dash import dash_table


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

        return dash_table.DataTable(frame.to_dict("records"))

    @property
    def get_factor_count(self) -> dash_table:
        cnt = self.data[self.factor].value_counts().to_frame().reset_index()
        cnt.columns = ["Sample type", "Count"]
        return dash_table.DataTable(cnt.to_dict("records"))
