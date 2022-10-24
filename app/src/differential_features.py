import os

import numpy as np
import pandas as pd
import scipy.stats as sts
from statsmodels.stats.multitest import fdrcorrection


class DifferentialFeatures:
    def __init__(self, data_frame: pd.DataFrame, samples: pd.Series, group_A: str, group_B: str):
        self.data_frame = data_frame
        self.variables = self.data_frame.index
        self.samples_A = samples[samples == group_A].index
        self.samples_B = samples[samples == group_B].index
        self.records = []
        self.stats_frame = None

    def run(self, alpha: float = 0.05) -> None:
        group_a = self.data_frame[self.samples_A]
        group_b = self.data_frame[self.samples_B]

        for var in self.variables:
            group_a_temp = group_a.loc[var].values.flatten()
            group_b_temp = group_b.loc[var].values.flatten()

            _, norm_a = sts.shapiro(group_a_temp)
            _, norm_b = sts.shapiro(group_b_temp)
            _, var_a_b = sts.levene(group_a_temp, group_b_temp)

            if norm_a > alpha and norm_b > alpha and var_a_b > alpha:
                status = "parametric"
                _, diff_pvalue = sts.ttest_ind(group_a_temp, group_b_temp, equal_var=True)

            elif norm_a > alpha >= var_a_b and norm_b > alpha:
                status = "parametric - not equal variance"
                _, diff_pvalue = sts.ttest_ind(group_a_temp, group_b_temp, equal_var=False)

            else:
                status = "non-parametric"
                _, diff_pvalue = sts.mannwhitneyu(group_a_temp, group_b_temp)

            log10_diff_pvalue = -np.log10(diff_pvalue)
            group_a_temp_mean = np.mean(group_a_temp)
            group_b_temp_mean = np.mean(group_b_temp)

            fc = group_a_temp_mean / group_b_temp_mean
            log_fc = np.log2(fc)

            delta = group_a_temp_mean - group_b_temp_mean
            abs_delta = abs(delta)

            record = {
                "Feature": var,
                "Mean(A)": group_a_temp_mean,
                "Mean(B)": group_b_temp_mean,
                "FC": fc,
                "log2(FC)": log_fc,
                "delta": delta,
                "|delta|": abs_delta,
                "Status": status,
                "p-value": diff_pvalue,
                "-log10(p-value)": log10_diff_pvalue,
            }

            self.records.append(record)

    def build_statistics_frame(self) -> None:
        frame = pd.DataFrame(self.records)
        _, frame["FDR"] = fdrcorrection(frame["p-value"])
        frame["Rank"] = frame["FDR"].map(lambda value: abs(np.log10(value))) * frame["|delta|"]
        frame["Rank"] = frame["Rank"] / frame["Rank"].sum()

        frame = frame.sort_values("Rank", ascending=False)
        frame = frame.set_index("Feature")
        self.stats_frame = frame

    def export(self, data_type: str, group_A: str, group_B: str) -> None:
        path = f"temp/{data_type.replace('/', '_')}_{group_A}_{group_B}.parquet"
        os.makedirs("temp/", exist_ok=True)
        self.stats_frame.to_parquet(path)
