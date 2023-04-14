import typing as t
from os.path import join

import numpy as np
import pandas as pd

from .utils import load_config

config = load_config()


class FrameOperations:
    def __init__(self, data_type: str, sample_types: t.Collection[str]):
        self.data_type = data_type
        self.sample_types = sample_types
        self.basic_path = config["base_path"]
        self.frame = None

    def load_1d(self, variable: str) -> t.Tuple[pd.DataFrame, str]:
        """
        Method loads frame of measurement, for one or many sample types.
        If variable is not in repository method returns empty frame.
        Additionally, the method returns a message describing the process.

        :param variable:
        :return pd.DataFrame, str:
        """

        frame = []

        for sample_type in self.sample_types:
            metadata = pd.read_pickle(join(self.basic_path, sample_type, "metadata.pkl"))

            if self.data_type == "Expression [RNA-seq]":
                if variable not in metadata["genes"]:
                    return (
                        pd.DataFrame(),
                        f"Gene: '{variable}' not found in '{sample_type}' repository",
                    )

                temporary_frame = pd.read_parquet(
                    join(self.basic_path, sample_type, "RNA-Seq.parquet")
                )

            if self.data_type == "Methylation [450K/EPIC]":
                if variable not in metadata["probes"]:
                    return (
                        pd.DataFrame(),
                        f"CpG: '{variable}' not found in '{sample_type}' repository",
                    )

                temporary_frame = pd.read_parquet(
                    join(self.basic_path, sample_type, "Methylation Array.parquet")
                )

            temporary_frame = temporary_frame.loc[variable, :].to_frame()
            temporary_frame["SampleType"] = sample_type

            frame.append(temporary_frame)

        frame = pd.concat(frame, axis=0)
        frame = frame.dropna(axis=0)  # drop rows (samples) with NaNs

        if frame.empty:
            return frame, "Data records for this specific requests are not available."

        return frame, "Status: done"

    def load_many(self, variables: t.List[str]) -> t.Tuple[pd.DataFrame, str]:
        """
        Method to load data from many sources [sample types] and extract specific set of variables.
        If set of variables [CpGs or genes] is not present in certain sample type method returns empty frame with
        appropriate message.

        :param variables:
        :return pd.DataFrame, str:
        """
        frame = []
        variables = set(variables)

        for sample_type in self.sample_types:
            if self.data_type == "Expression [RNA-seq]":
                temporary_frame = pd.read_parquet(
                    join(self.basic_path, sample_type, "RNA-Seq.parquet")
                )
            else:
                temporary_frame = pd.read_parquet(
                    join(self.basic_path, sample_type, "Methylation Array.parquet")
                )

            temporary_frame = temporary_frame.loc[
                list(variables.intersection(set(temporary_frame.index)))
            ].T

            if temporary_frame.empty:
                return (
                    pd.DataFrame(),
                    f"Selected set of variables is not available in {sample_type} dataset.",
                )

            temporary_frame["SampleType"] = sample_type
            frame.append(temporary_frame)

        frame = pd.concat(frame, axis=0).dropna(axis=1)  # drop columns (variables) with NaNs
        return frame, ""

    def load_mvf(self, threshold: float = 0.9) -> t.Tuple[pd.DataFrame, pd.Series]:
        """
        Method to load most variable features [mvf] across multiple sources [sample types].

        :param threshold:
        :return:
        """
        frame = []
        sample_frame = []
        for sample_type in self.sample_types:
            if self.data_type == "Expression [RNA-seq]":
                temporary_frame = pd.read_parquet(
                    join(self.basic_path, sample_type, "RNA-Seq.parquet")
                )
            else:
                temporary_frame = pd.read_parquet(
                    join(self.basic_path, sample_type, "Methylation Array.parquet")
                )

            if not temporary_frame.empty:
                frame.append(temporary_frame)
                samples = pd.Series(
                    [sample_type for _ in temporary_frame.columns],
                    index=temporary_frame.columns,
                    name="SampleType",
                )
                sample_frame.append(samples)

        frame = pd.concat(frame, axis=1).dropna(axis=0)  # drop rows (samples) with NaNs
        sample_frame = pd.concat(sample_frame)

        std = frame.std(axis=1)
        frame = frame.loc[std >= std.quantile(threshold)]
        return frame, sample_frame

    def load_met_exp_frame(self, gene: str, probe: str) -> t.Tuple[pd.DataFrame, str]:
        """
        Method to load frame with expression AND methylation data for requested sample type.
        If a probe or gene is not present in the requested repository or there are no common samples between
        methylation and expression datasets the method returns an empty frame, and appropriate message.

        :param gene:
        :param probe:
        :return:
        """
        meta = pd.read_pickle(join(self.basic_path, self.sample_types, "metadata.pkl"))

        if not meta["commonBetween"]:
            return pd.DataFrame(), "No common samples for this sample type."

        if gene not in meta["genes"]:
            return pd.DataFrame(), f"Gene: '{gene}' not found in requested repository."

        if probe not in meta["probes"]:
            return pd.DataFrame(), f"Probe: '{probe}' not found in requested repository."

        exp_frame = pd.read_parquet(join(self.basic_path, self.sample_types, "RNA-Seq.parquet"))
        exp_frame = exp_frame.loc[gene, list(meta["commonBetween"])]

        met_frame = pd.read_parquet(
            join(self.basic_path, self.sample_types, "Methylation Array.parquet")
        )
        met_frame = met_frame.loc[probe, list(meta["commonBetween"])]

        frame = pd.concat((exp_frame, met_frame), axis=1)
        frame = frame.dropna(axis=0)

        if frame.empty:
            return pd.DataFrame(), "Unfortunately this specific dataset is empty."

        return frame, "Status: done"

    @staticmethod
    def bin_variable(frame: pd.Series, n_bins: int) -> tuple[pd.Series, list[str]]:
        binned_frame = pd.qcut(frame, n_bins, precision=2)

        binned_frame = binned_frame.apply(
            lambda x: pd.Interval(left=round(x.left, 2), right=round(x.right, 2))
        )
        binned_frame = binned_frame.map(lambda bin_: f"Bin:{bin_}")

        return binned_frame

    @staticmethod
    def clean_sequence(sequence_of_variables: str, separator: str = "-->") -> t.List[str]:
        """
        Static method to parse raw input from text field.

        :param sequence_of_variables:
        :param separator:
        :return List[str]:
        """
        if separator in sequence_of_variables:
            sequence_of_variables = sequence_of_variables.split(separator)[1]

        variables = [var.strip() for var in sequence_of_variables.split(",")]
        variables = list(set(variables))

        return variables

    @staticmethod
    def scale(values: pd.Series, method: str) -> pd.Series:
        """
        Static method to scale feature.

        :param values:
        :param method:
        :return pd.Series:
        """
        if method == "Log10":
            return values.apply(np.log10)

        if method == "Log2":
            return values.apply(np.log2)

        if method == "Ln":
            return values.apply(np.log)

        if method == "Standard scaling":
            mean = np.mean(values)
            std = np.std(values)
            return (values - mean) / std

        return values
