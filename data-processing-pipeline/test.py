import json
import multiprocessing
import pickle
from glob import glob
from os.path import exists, join
from pathlib import Path

import pandas as pd
from tqdm import tqdm

with open("config.json", "r", encoding="utf-8") as file:
    config = json.load(file)


def test_config_file() -> None:
    """
    Test to analyse if config file parameters are correctly specified.

    :return:
    """
    assert (
        config["MAX_SAMPLES_PER_SAMPLE_GROUP"] > config["MIN_SAMPLES_PER_SAMPLE_GROUP"]
    ), "MAX and MIN params wrongly specified."
    assert multiprocessing.cpu_count() >= config["N_PROCESS"], "N_PROCESS exceed limit."
    assert exists(config["GDC_TRANSFER_TOOL_EXECUTABLE"]), "Can`t find GDC tool."
    assert config["FILES_LIMIT"] > 0, "Negative limit of files."


def test_tree_directory() -> None:
    """
    Test to check if local data repository directory is correct.

    :return:
    """
    for path in config["DIRECTORY_TREE"]:
        assert exists(path), f"Can`t find {path}"


def test_sample_sheet_consistency() -> None:
    """
    Test to check sample sheet construction.

    :return:
    """
    sample_sheet = pd.read_parquet(config["SAMPLE_SHEET_FILE"])
    assert False is sample_sheet.empty, "Sample sheet is empty."
    assert sample_sheet.id.nunique() == sample_sheet.shape[0], "Files ids non unique."
    assert (
        config["SAMPLE_GROUP_ID"] in sample_sheet.columns
    ), "Lack of sample group id information in sample sheet."

    processed_files = glob("data/processed/*/*.parquet")
    assert processed_files, "Can`t find parquet files in processed directory."

    for source in tqdm(processed_files):
        sample_group = Path(source).parent.name
        strategy = Path(source).name.replace(".parquet", "")

        observed_samples = pd.read_parquet(source)
        observed_samples = set(observed_samples.columns)

        expected_samples = sample_sheet[sample_sheet.experimental_strategy == strategy]
        expected_samples = expected_samples[
            expected_samples[config["SAMPLE_GROUP_ID"]] == sample_group
        ]
        expected_samples = set(expected_samples.case_id)

        assert observed_samples == expected_samples, f"Sample sheet and are not consistent."


def test_samples_names_per_frame() -> None:
    """
    Test to check if samples names in processed frames are consistent with sample sheet.

    :return:
    """
    sample_sheet = pd.read_parquet(config["SAMPLE_SHEET_FILE"])

    for source in tqdm(glob("data/processed/*/*.parquet")):
        stype = Path(source).parent.name
        e_strategy = Path(source).name.replace(".parquet", "")

        temp_sample_sheet = sample_sheet[
            (sample_sheet[config["SAMPLE_GROUP_ID"]] == stype)
            & (sample_sheet["experimental_strategy"] == e_strategy)
        ]

        expected_samples_per_samples_types = set(temp_sample_sheet.case_id)

        samples = pd.read_parquet(source).columns.tolist()
        samples = set(samples)

        assert samples.issubset(
            expected_samples_per_samples_types
        ), f"Non consistent names of samples in processed frames."


def test_manifests_files() -> None:
    """
    Test to check if manifests files are consistent with sample sheet.

    :return:
    """
    sample_sheet = pd.read_parquet(config["SAMPLE_SHEET_FILE"])
    manifests_files = glob(join(config["INTERIM_BASE_PATH"], "*", "*", "manifest.txt"))
    assert manifests_files, "Can`t find manifests files."

    for source in manifests_files:
        observed_files = set(pd.read_table(source)["id"])

        experimental_strategy = Path(source).parent.name
        sample_group = Path(source).parent.parent.name

        expected_files = sample_sheet[
            (sample_sheet[config["SAMPLE_GROUP_ID"]] == sample_group)
            & (sample_sheet["experimental_strategy"] == experimental_strategy)
        ]

        expected_files = set(expected_files["id"])
        assert expected_files == observed_files, f"Non consistent manifests files."


def test_meta_samples_collection_1() -> None:
    """
    Test to check if samples in cleaned sample sheet are subset of samples collections objects.

    :return:
    """
    sample_sheet = pd.read_parquet(config["SAMPLE_SHEET_FILE"])

    with open(join(config["META_PATH"], "samples_collection.pkl"), "rb") as source:
        collections = pickle.load(source)

    for stype, collection in collections.items():
        temp_sample_sheet = sample_sheet[sample_sheet.SAMPLE_GROUP_ID == stype]

        all_met_samples = collection.methylation_samples
        all_exp_samples = collection.expression_samples

        selected_exp_samples = set(
            temp_sample_sheet[temp_sample_sheet.experimental_strategy == "RNA-Seq"].index
        )
        selected_met_samples = set(
            temp_sample_sheet[temp_sample_sheet.experimental_strategy == "Methylation Array"].index
        )

        assert len(selected_met_samples) <= 50, "Wrong number of met samples in final sample sheet"
        assert len(selected_exp_samples) <= 50, "Wrong number of exp samples in final sample sheet"

        assert selected_exp_samples.issubset(
            all_exp_samples
        ), "Cleaned sample sheet exp files should be a subset of all Exp files."
        assert selected_met_samples.issubset(
            all_met_samples
        ), "Cleaned sample sheet met files should be a subset of all Met files."


def test_meta_samples_collection_2() -> None:
    """
    Test to check if samples in met and exp frames are subset of samples collections objects.

    :return:
    """

    with open(join(config["META_PATH"], "samples_collection.pkl"), "rb") as source:
        collections = pickle.load(source)

    for name, collection in tqdm(collections.items()):
        meth_path = join(config["PROCESSED_DIR"], name, "Methylation Array.parquet")
        exp_path = join(config["PROCESSED_DIR"], name, "RNA-Seq.parquet")

        if exists(exp_path):
            all_exp_samples = collection.expression_samples

            exp_samples = pd.read_parquet(exp_path).columns
            exp_samples = set(exp_samples)
            assert exp_samples.issubset(
                all_exp_samples
            ), "Exp samples in exp frame are not subset of collection object."

        if exists(meth_path):
            all_met_samples = collection.methylation_samples

            met_samples = pd.read_parquet(meth_path).columns
            met_samples = set(met_samples)
            assert met_samples.issubset(
                all_met_samples
            ), "Met samples in met frame are not subset of collection object."

        if exists(meth_path) and exists(exp_path):
            all_common_samples = collection.common_samples

            common = exp_samples.intersection(met_samples)
            assert common.issubset(
                all_common_samples
            ), "Common samples between met and exp frames are not subset of collection object."


def test_metadata() -> None:
    """
    Test to check if metadata objects contains an appropriate sets of genes, probes and samples in comparison to
    met and exp frames.

    :return:
    """
    for source in tqdm(glob("data/processed/*/metadata")):
        metadata = pd.read_pickle(source)
        expected_sample_group = Path(source).parent.name

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
    """
    Test to check if global metadata object contains an appropriate number of sample types, met frames and exp frames.

    :return:
    """
    global_metadata = pd.read_pickle("data/processed/metadataGlobal")
    expected_number_of_stypes = len(glob("data/processed/*/"))

    assert (
        expected_number_of_stypes == global_metadata["Number_of_sample_types"]
    ), "Wrong number of samples types."

    expected_exp_files = glob("data/processed/*/RNA-Seq.parquet")
    expected_exp_files = {Path(source).parent.name for source in expected_exp_files}

    assert expected_exp_files == set(
        global_metadata["Expression_files_present"]
    ), "Set of expression frames wrongly specified."

    expected_met_files = glob("data/processed/*/Methylation Array.parquet")
    expected_met_files = {Path(source).parent.name for source in expected_met_files}

    assert expected_met_files == set(
        global_metadata["Methylation_files_present"]
    ), "Set of methylation frames wrongly specified."
