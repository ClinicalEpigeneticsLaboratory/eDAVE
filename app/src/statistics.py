from io import StringIO

import pandas as pd
from dash import dash_table
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
