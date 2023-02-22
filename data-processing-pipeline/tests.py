import json
import multiprocessing
import pickle
from glob import glob
from os.path import exists, join
from pathlib import Path

import pandas as pd
from tqdm import tqdm

with open("config.json", "r") as file:
    config = json.load(file)


def test_config_file() -> None:
    assert (
        config["MAX_SAMPLES_PER_SAMPLE_GROUP"] > config["MIN_SAMPLES_PER_SAMPLE_GROUP"]
    ), "MAX and MIN params wrongly specified."
    assert multiprocessing.cpu_count() >= config["N_PROCESS"], "N_PROCESS exceed limit."
    assert exists(config["GDC_TRANSFER_TOOL_EXECUTABLE"]), "Can`t find GDC tool."
    assert config["FILES_LIMIT"] > 0, "Negative limit of files."


def test_tree_directory() -> None:
    for path in config["DIRECTORY_TREE"]:
        assert exists(path), f"Can`t find {path}"


def test_sample_sheet_consistency() -> None:
    sample_sheet = pd.read_parquet(config["SAMPLE_SHEET_FILE"])
    assert False == sample_sheet.empty, "Sample sheet is empty."
    assert (
        config["SAMPLE_GROUP_ID"] in sample_sheet.columns
    ), "Lack of sample group id information in sample sheet."

    for source in tqdm(glob("data/processed/*/*.parquet")):
        sample_group = Path(source).parent.name
        strategy = Path(source).name.replace(".parquet", "")

        observed_samples = pd.read_parquet(source)
        observed_samples = set(observed_samples.columns)

        expected_samples = sample_sheet[sample_sheet.experimental_strategy == strategy]
        expected_samples = expected_samples[
            expected_samples[config["SAMPLE_GROUP_ID"]] == sample_group
        ]
        expected_samples = set(expected_samples.index)

        assert (
            expected_samples == observed_samples
        ), f"Sample sheet and {source}-{strategy} are not consistent."


def test_samples_names_per_frame() -> None:
    sample_sheet = pd.read_parquet(config["SAMPLE_SHEET_FILE"])
    sample_sheet = set(sample_sheet.index)

    for source in tqdm(glob("data/processed/*/*.parquet")):
        samples = pd.read_parquet(source).columns.tolist()

        samples = set(samples)
        assert samples.issubset(sample_sheet), f"Non consistent names of samples in frame {source}."


def test_manifests_files() -> None:
    sample_sheet = pd.read_parquet(config["SAMPLE_SHEET_FILE"])
    for source in glob(join(config["INTERIM_BASE_PATH"], "*", "*", "manifest.txt")):
        observed_files = set(pd.read_table(source)["id"])

        experimental_strategy = Path(source).parent.name
        sample_group = Path(source).parent.parent.name

        expected_files = sample_sheet[
            (sample_sheet[config["SAMPLE_GROUP_ID"]] == sample_group)
            & (sample_sheet["experimental_strategy"] == experimental_strategy)
        ]
        expected_files = set(expected_files["id"])

        assert expected_files == observed_files, f"Non consistent manifest file {source}"


def test_meta_samples_collection() -> None:

    with open(join(config["META_PATH"], "samples_collection.pkl"), "rb") as source:
        collections = pickle.load(source)

    for name, collection in tqdm(collections.items()):
        meth_path = join(config["PROCESSED_DIR"], name, "Methylation Array.parquet")
        exp_path = join(config["PROCESSED_DIR"], name, "RNA-Seq.parquet")

        if exists(meth_path):
            met_samples = pd.read_parquet(meth_path).columns
            met_samples = set(met_samples)
            assert (
                met_samples == collection.methylation_samples
            ), "Met samples in collection object wrongly specified."

        if exists(exp_path):
            exp_samples = pd.read_parquet(exp_path).columns
            exp_samples = set(exp_samples)
            assert (
                exp_samples == collection.expression_samples
            ), "Exp samples in collection object wrongly specified."

        if exists(meth_path) and exists(exp_path):
            common = exp_samples.intersection(met_samples)
            assert (
                common == collection.common_samples
            ), "Common samples in collection object wrongly specified."


def test_metadata() -> None:
    for source in tqdm(glob("data/processed/*/metadata")):
        metadata = pd.read_pickle(source)
        expected_sample_group = Path(source).parent.name
        print(expected_sample_group, metadata["SampleGroup"])

        assert (
            expected_sample_group == metadata["SampleGroup"]
        ), f"Wrongly specified name of samples group."
        if metadata["genes"]:
            frame = pd.read_parquet(join(Path(source).parent, "RNA-Seq.parquet"))
            genes = set(frame.index)
            samples = set(frame.columns)

            assert genes == metadata["genes"], "Genes set wrongly specified."
            assert (
                samples == metadata["expressionSamples"]
            ), "Expression samples set wrongly specified."

        if metadata["probes"]:
            frame = pd.read_parquet(join(Path(source).parent, "Methylation Array.parquet"))
            probes = set(frame.index)
            samples = set(frame.columns)

            assert probes == metadata["probes"], "Probes set wrongly specified."
            assert (
                samples == metadata["methylationSamples"]
            ), "Methylation samples set wrongly specified."


def test_global_metadata() -> None:
    global_metadata = pd.read_pickle("data/processed/metadataGlobal")

    expected_number_of_stypes = len(glob("data/processed/*/"))
    assert (
        expected_number_of_stypes == global_metadata["Number_of_sample_types"]
    ), "Wrong number of samples types."

    expected_exp_files = glob("data/processed/*/RNA-Seq.parquet")
    expected_exp_files = set([Path(source).parent.name for source in expected_exp_files])
    assert expected_exp_files == set(
        global_metadata["Expression_files_present"]
    ), "Wrong collection of expression frames."

    expected_met_files = glob("data/processed/*/Methylation Array.parquet")
    expected_met_files = set([Path(source).parent.name for source in expected_met_files])
    assert expected_met_files == set(
        global_metadata["Methylation_files_present"]
    ), "Wrong collection of methylation frames."
