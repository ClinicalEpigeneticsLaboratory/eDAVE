import json
import multiprocessing
import pickle
from glob import glob
from os.path import exists, join
from pathlib import Path

import pandas as pd
from src.collector import SamplesCollector
from tqdm import tqdm

with open("config.json", "r", encoding="utf-8") as file:
    config = json.load(file)


def test_collector_1() -> None:
    """
    Test to check scenario when common samples > min samples, final met and exp samples should contain the same samples.

    :return:
    """
    methylation_samples = ["A", "B", "C", "D", "E", "F", "G"]
    expression_samples = ["A", "B", "C", "D", "E", "F", "G"]
    common = list(set(methylation_samples).intersection(set(expression_samples)))

    sa = SamplesCollector(
        min_samples=5,
        max_samples=10,
        name="",
        methylation_samples=methylation_samples,
        expression_samples=expression_samples,
        common_samples=common,
    )

    exp = sa.get_samples_list("RNA-Seq")
    met = sa.get_samples_list("Methylation Array")

    assert met == exp == common, "Met and exp should be equal to common set."


def test_collector_2() -> None:
    """
    Test to check if met and exp < min samples, so final met and exp lists should be empty.

    :return:
    """
    methylation_samples = ["A", "B"]
    expression_samples = ["A", "B"]
    common = list(set(methylation_samples).intersection(set(expression_samples)))

    sa = SamplesCollector(
        min_samples=3,
        max_samples=10,
        name="",
        methylation_samples=methylation_samples,
        expression_samples=expression_samples,
        common_samples=common,
    )

    exp = sa.get_samples_list("RNA-Seq")
    met = sa.get_samples_list("Methylation Array")

    assert met == exp == [], "Met and exp should be empty sets."


def test_collector_3() -> None:
    """
    Test to check if met > max samples and exp < min samples, so final met list should be subset of initial met and exp
    list should be empty.

    :return:
    """
    methylation_samples = ["A", "B", "C", "D", "E", "F", "G"]
    expression_samples = ["A", "B"]
    common = list(set(methylation_samples).intersection(set(expression_samples)))

    sa = SamplesCollector(
        min_samples=3,
        max_samples=5,
        name="",
        methylation_samples=methylation_samples,
        expression_samples=expression_samples,
        common_samples=common,
    )

    exp = sa.get_samples_list("RNA-Seq")
    met = sa.get_samples_list("Methylation Array")

    assert set(met).issubset(set(methylation_samples)), "Wrongly specified met set."
    assert len(met) == len(set(met)), "Met set contains non unique objects."
    assert len(met) == 5, "Wrong met set length."
    assert exp == [], "Exp set should be empty."


def test_collector_4() -> None:
    """
    Test to check if max samples > met > min samples and exp < min samples, so final met list should be equal to initial
    and exp list should be empty.

    :return:
    """
    methylation_samples = ["A", "B", "C"]
    expression_samples = ["A", "B"]
    common = list(set(methylation_samples).intersection(set(expression_samples)))

    sa = SamplesCollector(
        min_samples=3,
        max_samples=10,
        name="",
        methylation_samples=methylation_samples,
        expression_samples=expression_samples,
        common_samples=common,
    )

    exp = sa.get_samples_list("RNA-Seq")
    met = sa.get_samples_list("Methylation Array")

    assert met == methylation_samples, "Wrongly specified met set."
    assert exp == [], "Exp set should be empty."


def test_collector_5() -> None:
    """
    Test to check if common > min samples so met end exp should contain only common samples.

    :return:
    """
    methylation_samples = ["A", "B", "C", "D", "E", "F"]
    expression_samples = ["A", "B", "C", "D", "E"]
    common = list(set(methylation_samples).intersection(set(expression_samples)))

    sa = SamplesCollector(
        min_samples=3,
        max_samples=5,
        name="",
        methylation_samples=methylation_samples,
        expression_samples=expression_samples,
        common_samples=common,
    )

    exp = sa.get_samples_list("RNA-Seq")
    met = sa.get_samples_list("Methylation Array")

    assert met == exp == common, "Wrongly specified met or exp sets."
    assert len(met) == 5, "Wrong number of samples per set."


def test_config_file() -> None:
    """
    Test to analyse if config file parameters are correctly specified.

    :return:
    """
    assert (
        config["MAX_SAMPLES_PER_SAMPLE_GROUP"] > config["MIN_SAMPLES_PER_SAMPLE_GROUP"]
    ), "MAX and MIN params wrongly specified."
    assert multiprocessing.cpu_count() * 3 >= config["N_PROCESS"], "N_PROCESS exceed limit."
    assert exists(config["GDC_TRANSFER_TOOL_EXECUTABLE"]), "Can`t find GDC tool."
    assert config["FILES_LIMIT"] > 0, "Negative limit of files."


def test_tree_directory() -> None:
    """
    Test to check if local data repository directory is correct.

    :return:
    """
    for path in config["DIRECTORY_TREE"]:
        assert exists(path), f"Can`t find {path}"


def test_sample_sheet_construction() -> None:
    """
    Test to check sample sheet construction.

    :return:
    """
    sample_sheet = pd.read_parquet(config["SAMPLE_SHEET_FILE"])
    assert False is sample_sheet.empty, "Sample sheet is empty."
    assert sample_sheet.index.nunique() == sample_sheet.shape[0], "Files ids non unique."
    assert (
        config["SAMPLE_GROUP_ID"] in sample_sheet.columns
    ), "Lack of sample group id information in sample sheet."


def test_samples_names_per_frame() -> None:
    """
    Test to check if samples names in processed frames [met and exp] are consistent with sample sheet.

    :return:
    """
    sample_sheet = pd.read_parquet(config["SAMPLE_SHEET_FILE"])
    processed_files = glob("data/processed/*/*.parquet")

    assert processed_files, "Can`t find parquet files in processed directory."

    for source in tqdm(processed_files):
        stype = Path(source).parent.name
        e_strategy = Path(source).name.replace(".parquet", "")

        temp_sample_sheet = sample_sheet[
            (sample_sheet[config["SAMPLE_GROUP_ID"]] == stype)
            & (sample_sheet["experimental_strategy"] == e_strategy)
        ]

        expected_samples_per_samples_types = set(temp_sample_sheet.case_id)

        observed_samples = pd.read_parquet(source).columns.tolist()
        observed_samples = set(observed_samples)

        assert (
            observed_samples == expected_samples_per_samples_types
        ), "Non consistent names of samples [case ids] between processed frames and the sample sheet."


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

        expected_files = set(expected_files.index)
        assert (
            expected_files == observed_files
        ), "Non consistent manifests files with sample sheet in terms of files id."


def test_meta_samples_collection_1() -> None:
    """
    Test to check if samples in cleaned sample sheet are consistent with SamplesCollector objects.

    :return:
    """
    sample_sheet = pd.read_parquet(config["SAMPLE_SHEET_FILE"])

    with open(join(config["META_PATH"], "samples_collection.pkl"), "rb") as source:
        collections = pickle.load(source)

    for stype, collection in collections.items():
        temp_sample_sheet = sample_sheet[sample_sheet.SAMPLE_GROUP_ID == stype]

        expected_met_samples = set(collection.get_samples_list("Methylation Array"))
        expected_exp_samples = set(collection.get_samples_list("RNA-Seq"))

        selected_exp_samples = set(
            temp_sample_sheet[temp_sample_sheet.experimental_strategy == "RNA-Seq"]["case_id"]
        )
        selected_met_samples = set(
            temp_sample_sheet[temp_sample_sheet.experimental_strategy == "Methylation Array"][
                "case_id"
            ]
        )

        assert len(selected_met_samples) <= 50, "Wrong number of met samples in final sample sheet"
        assert len(selected_exp_samples) <= 50, "Wrong number of exp samples in final sample sheet"

        assert (
            selected_exp_samples == expected_exp_samples
        ), "Cleaned sample sheet exp files should be a subset of all Exp files."
        assert (
            selected_met_samples == expected_met_samples
        ), "Cleaned sample sheet met files should be a subset of all Met files."


def test_meta_samples_collection_2() -> None:
    """
    Test to check if samples in met and exp frames are consistent with SamplesCollector objects.

    :return:
    """

    with open(join(config["META_PATH"], "samples_collection.pkl"), "rb") as source:
        collections = pickle.load(source)

    for name, collection in tqdm(collections.items()):
        meth_path = join(config["PROCESSED_DIR"], name, "Methylation Array.parquet")
        exp_path = join(config["PROCESSED_DIR"], name, "RNA-Seq.parquet")

        if exists(exp_path):
            expected_exp_samples = set(collection.get_samples_list("RNA-Seq"))

            observed_exp_samples = pd.read_parquet(exp_path).columns
            observed_exp_samples = set(observed_exp_samples)

            assert (
                observed_exp_samples == expected_exp_samples
            ), "Exp samples in exp frame are not consistent with exp samples in collection object."

        if exists(meth_path):
            expected_met_samples = set(collection.get_samples_list("Methylation Array"))

            observed_met_samples = pd.read_parquet(meth_path).columns
            observed_met_samples = set(observed_met_samples)
            assert (
                observed_met_samples == expected_met_samples
            ), "Met samples in met frame are not consistent with met samples in collection object."


def test_metadata() -> None:
    """
    Test to check if metadata objects contains an appropriate sets of genes, probes and samples in comparison to
    met and exp frames.

    :return:
    """
    for source in tqdm(glob("data/processed/*/metadata.pkl")):
        metadata = pd.read_pickle(source)
        expected_sample_group = Path(source).parent.name

        assert (
            expected_sample_group == metadata["SampleGroup"]
        ), "Wrongly specified name of samples group."

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
    global_metadata = pd.read_pickle(config["METADATA_GLOBAL_FILE"])
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
