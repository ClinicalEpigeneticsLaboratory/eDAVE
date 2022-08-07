import typing as t
from os.path import join

import numpy as np
import pandas as pd

from .utils import load_config

config = load_config()


class FrameOperations:
    def __init__(self, data_type: str, sample_types: t.Union[t.Collection[str], str]):
        self.data_type = data_type
        self.sample_types = sample_types
        self.basic_path = config["base_path"]
        self.frame = None

    def load_1d(self, variable: str) -> t.Tuple[pd.DataFrame, str]:
        """
        Methods load frame of measurement, for one or multiple sample types.
        If variable is not in repository returns empty frame or selected data_type does not exists returns empty frame.
        Additionally, the function return a message describing the process.
        """

        frame = []

        for sample_type in self.sample_types:
            metadata = pd.read_pickle(join(self.basic_path, sample_type, "metadata"))

            if self.data_type == "Expression [RNA-seq]":

                if variable not in metadata["genes"]:
                    return (
                        pd.DataFrame(),
                        f"Gene: '{variable}' not found in '{sample_type}' repository",
                    )

                temporary_frame = pd.read_parquet(join(self.basic_path, sample_type, "Exp.parquet"))

            elif self.data_type == "Methylation [450K/EPIC]":
                if variable not in metadata["probes"]:
                    return (
                        pd.DataFrame(),
                        f"CpG: '{variable}' not found in '{sample_type}' repository",
                    )

                temporary_frame = pd.read_parquet(join(self.basic_path, sample_type, "Met.parquet"))

            else:
                temporary_frame = pd.DataFrame(), f"Data type: '{self.data_type}' does not exists"

            temporary_frame = temporary_frame.loc[variable, :].to_frame()
            temporary_frame["SampleType"] = sample_type

            frame.append(temporary_frame)

        frame = pd.concat(frame, axis=0)
        frame = frame.dropna(axis=0)  # drop rows (samples) with NaNs

        return frame, "Status: done"

    def load_many(self, variables: t.List[str]) -> pd.DataFrame:
        """
        Function to load ane extract specific set of variables from multiple sources [sample types].
        """
        frame = []
        variables = set(variables)

        for sample_type in self.sample_types:
            if self.data_type == "Expression [RNA-seq]":
                temporary_frame = pd.read_parquet(join(self.basic_path, sample_type, "Exp.parquet"))
            else:
                temporary_frame = pd.read_parquet(join(self.basic_path, sample_type, "Met.parquet"))

            temporary_frame = temporary_frame.loc[
                list(variables.intersection(set(temporary_frame.index)))
            ].T

            if not temporary_frame.empty:
                temporary_frame["SampleType"] = sample_type
                frame.append(temporary_frame)

        frame = pd.concat(frame, axis=0).dropna(axis=1)  # drop columns (variables) with NaNs
        return frame

    def load_met_exp_frame(self, gene: str, probe: str) -> t.Tuple[pd.DataFrame, str]:
        """
        Function to load frame with expression and methylation data for common samples in requested sample type.
        If a probe or gene is not present in the requested repository or there are no common samples between methylation
        and expression data sets the function returns an empty frame.
        """
        meta = pd.read_pickle(join(self.basic_path, self.sample_types, "metadata"))

        if len(meta["commonBetween"]) == 0:
            return pd.DataFrame(), "No common samples for this sample type"

        if gene not in meta["genes"]:
            return pd.DataFrame(), f"Gene: '{gene}' not found in requested repository"

        if probe not in meta["probes"]:
            return pd.DataFrame(), f"Probe: '{probe}' not found in requested repository"

        exp_frame = pd.read_parquet(join(self.basic_path, self.sample_types, "Exp.parquet"))
        exp_frame = exp_frame.loc[gene, list(meta["commonBetween"])]

        met_frame = pd.read_parquet(join(self.basic_path, self.sample_types, "Met.parquet"))
        met_frame = met_frame.loc[probe, list(meta["commonBetween"])]

        frame = pd.concat((exp_frame, met_frame), axis=1)
        frame = frame.dropna(axis=0)

        return frame, "Status: done"

    @staticmethod
    def clean_sequence(sequence_of_variables) -> t.List[str]:
        """
        Function to parse raw input from text area.
        """
        sequence_of_variables = str(sequence_of_variables)
        sequence_of_variables = sequence_of_variables.replace("Eg.", "")
        variables = [var.strip() for var in sequence_of_variables.split(",")]
        variables = list(set(variables))

        return variables

    @staticmethod
    def scale(values, method):
        """
        Function to scale 1-D variable.
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
