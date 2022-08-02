import json
from os.path import join

import typing as t
import numpy as np
import pandas as pd

config = json.load(open("../config.json", "r"))


class FrameOperations:
    """
    Class implementing basic frame operations eg. loading.
    """

    def __init__(self, data_type: str, sample_types: t.Union[t.Collection[str], str]):
        self.data_type = data_type
        self.sample_types = sample_types
        self.basic_path = config["base_path"]
        self.frame = None

    @staticmethod
    def __check_if_in_index(frame: t.Union[pd.DataFrame, pd.Series], variable: str):
        if variable not in set(frame.index):
            return False

        return True

    def load_1d(self, variable: str) -> pd.DataFrame:
        frame = []

        for sample_type in self.sample_types:
            metadata = pd.read_pickle(join(self.basic_path, sample_type, "metadata"))

            if self.data_type == "Expression [RNA-seq]":

                if variable not in metadata["genes"]:
                    return pd.DataFrame()

                temporary_frame = pd.read_parquet(
                    join(self.basic_path, sample_type, "Exp.parquet")
                )

            elif self.data_type == "Methylation [450K/EPIC]":
                if variable not in metadata["probes"]:
                    return pd.DataFrame()

                temporary_frame = pd.read_parquet(
                    join(self.basic_path, sample_type, "Met.parquet")
                )

            else:
                temporary_frame = pd.DataFrame()

            temporary_frame = temporary_frame.loc[variable, :].to_frame()
            temporary_frame["SampleType"] = sample_type

            frame.append(temporary_frame)

        frame = pd.concat(frame, axis=0)
        return frame

    def load_many(self, variables: t.List[str]) -> pd.DataFrame:
        frame = []
        variables = set(variables)

        for sample_type in self.sample_types:
            if self.data_type == "Expression [RNA-seq]":
                temporary_frame = pd.read_parquet(
                    join(self.basic_path, sample_type, "Exp.parquet")
                )
            else:
                temporary_frame = pd.read_parquet(
                    join(self.basic_path, sample_type, "Met.parquet")
                )

            temporary_frame = temporary_frame.loc[
                list(variables.intersection(set(temporary_frame.index)))
            ].T
            temporary_frame["SampleType"] = sample_type

            frame.append(temporary_frame)

        frame = pd.concat(frame, axis=0).dropna()
        return frame

    def load_met_exp_frame(
        self, gene: str, probe: str
    ) -> t.Tuple[bool, t.Union[str, pd.DataFrame]]:

        meta = pd.read_pickle(join(self.basic_path, self.sample_types, "metadata"))

        if len(meta["commonBetween"]) == 0:
            return True, "No common samples for this sample type"

        if gene in meta["genes"] and probe in meta["probes"]:

            exp_frame = pd.read_parquet(
                join(self.basic_path, self.sample_types, "Exp.parquet")
            )
            exp_frame = exp_frame.loc[gene, list(meta["commonBetween"])]

            met_frame = pd.read_parquet(
                join(self.basic_path, self.sample_types, "Met.parquet")
            )
            met_frame = met_frame.loc[probe, list(meta["commonBetween"])]

            frame = pd.concat((exp_frame, met_frame), axis=1)

            return False, frame

        if gene not in meta["genes"]:
            return True, f"{gene} not found in requested repository"

        return True, f"{probe} not found in requested repository"

    @staticmethod
    def clean_sequence(sequence_of_variables) -> t.List[str]:
        return [var.strip() for var in sequence_of_variables.split(",")]

    @staticmethod
    def scale(values, method):
        if method == "Log10":
            return values.apply(np.log10)

        elif method == "Log2":
            return values.apply(np.log2)

        elif method == "Ln":
            return values.apply(np.log)

        elif method == "Standard scaling":
            mean = np.mean(values)
            std = np.std(values)
            return (values - mean) / std

        else:
            return values

    @staticmethod
    def scale_many(data: pd.DataFrame, method: str, factor: str) -> pd.DataFrame:
        for var in data.columns:
            if var != factor:
                data[var] = FrameOperations.scale(data[var], method)
        return data
