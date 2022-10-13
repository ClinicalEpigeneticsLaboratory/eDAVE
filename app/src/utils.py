import json
from os.path import exists, join

import pandas as pd


def response_multidim(variables: list, frame: pd.DataFrame) -> str:
    common = set(variables).intersection(frame.columns)
    msg = f"{len(common)}/{len(variables)} inputted variables present in selected sample types:"
    msg = msg + "\n" + ", ".join(common)

    return msg


def check_if_exists(data_path, sample_type: str, file_type: str) -> bool:
    path = join(data_path, sample_type, file_type)
    return exists(path)


def load_config(path: str = "config.json") -> dict:
    with open(path, "r", encoding="utf-8") as config_file:
        return json.load(config_file)
