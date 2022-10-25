import numpy as np
import pandas as pd
import scipy.stats as sts
from statsmodels.stats.multitest import fdrcorrection


class DifferentialFeatures:
    def __init__(
        self,
        data_type: str,
        data_frame: pd.DataFrame,
        samples: pd.Series,
        group_A: str,
        group_B: str,
        alpha: float,
        effect_size: float,
    ):
        self.data_type = data_type
        self.data_frame = data_frame
        self.group_A = group_A
        self.group_B = group_B
        self.samples_A = samples[samples == group_A].index
        self.samples_B = samples[samples == group_B].index
        self.variables = self.data_frame.index
        self.alpha = alpha
        self.effect_size = effect_size
        self.stats_frame = None
        self.records = []

    def identify_differential_features(self) -> None:
        group_a = self.data_frame[self.samples_A]
        group_b = self.data_frame[self.samples_B]

        for var in self.variables:
            group_a_temp = group_a.loc[var].values.flatten()
            group_b_temp = group_b.loc[var].values.flatten()

            _, norm_a = sts.shapiro(group_a_temp)
            _, norm_b = sts.shapiro(group_b_temp)
            _, var_a_b = sts.levene(group_a_temp, group_b_temp)

            if norm_a > self.alpha and norm_b > self.alpha and var_a_b > self.alpha:
                status = "parametric"
                _, diff_pvalue = sts.ttest_ind(group_a_temp, group_b_temp, equal_var=True)

            elif norm_a > self.alpha >= var_a_b and norm_b > self.alpha:
                status = "parametric - not equal variance"
                _, diff_pvalue = sts.ttest_ind(group_a_temp, group_b_temp, equal_var=False)

            else:
                status = "non-parametric"
                _, diff_pvalue = sts.mannwhitneyu(group_a_temp, group_b_temp)

            log10_diff_pvalue = -np.log10(diff_pvalue)
            group_a_temp_mean = np.mean(group_a_temp)
            group_b_temp_mean = np.mean(group_b_temp)

            if group_b_temp_mean != 0:
                fc = group_a_temp_mean / group_b_temp_mean
                log_fc = np.log2(fc)
            else:
                fc = np.NaN
                log_fc = np.NaN

            delta = group_a_temp_mean - group_b_temp_mean
            abs_delta = abs(delta)

            record = {
                "Feature": var,
                f"Mean({self.group_A})": group_a_temp_mean,
                f"Mean({self.group_B})": group_b_temp_mean,
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
        frame["-log10(FDR)"] = frame["FDR"].map(lambda value: -np.log10(value))
        frame = frame.sort_values("-log10(FDR)", ascending=False)
        frame = frame.set_index("Feature")

        if self.data_type == "Expression [RNA-seq]":
            frame["DEG/DMP"] = (frame["FDR"] <= self.alpha) & (
                frame["log2(FC)"].abs() >= self.effect_size
            )
        else:
            frame["DEG/DMP"] = (frame["FDR"] <= self.alpha) & (
                frame["delta"].abs() >= self.effect_size
            )

        self.stats_frame = frame

    def export(self, path: str) -> None:
        self.stats_frame.to_parquet(path)
