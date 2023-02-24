import json
import pickle
from glob import glob
from os import makedirs
from os.path import exists, join
from pathlib import Path
from subprocess import call
from typing import Set

import numpy as np
import pandas as pd
import requests
from prefect import flow, get_run_logger, task
from src.exceptions import RepositoryExistsError
from src.records import GlobalMetaRecord, MetaRecord, RepositorySummary
from src.sample_collection import SamplesCollection
from src.utils import load_config
from tqdm import tqdm

config = load_config()

GDC_TRANSFER_TOOL_EXECUTABLE = config["GDC_TRANSFER_TOOL_EXECUTABLE"]
MIN_SAMPLES_PER_SAMPLE_GROUP = config["MIN_SAMPLES_PER_SAMPLE_GROUP"]
MAX_SAMPLES_PER_SAMPLE_GROUP = config["MAX_SAMPLES_PER_SAMPLE_GROUP"]
GDC_RAW_RESPONSE_FILE = config["GDC_RAW_RESPONSE_FILE"]
METADATA_GLOBAL_FILE = config["METADATA_GLOBAL_FILE"]
MIN_COMMON_SAMPLES = config["MIN_COMMON_SAMPLES"]
INTERIM_BASE_PATH = config["INTERIM_BASE_PATH"]
SAMPLE_SHEET_FILE = config["SAMPLE_SHEET_FILE"]
SUMMARY_METAFILE = config["SUMMARY_METAFILE"]
SAMPLE_GROUP_ID = config["SAMPLE_GROUP_ID"]
FILTERS_CONFIG = config["FILTERS_CONFIG"]
BASE_DATA_PATH = config["BASE_DATA_PATH"]
DIRECTORY_TREE = config["DIRECTORY_TREE"]
FIELDS_CONFIG = config["FIELDS_CONFIG"]
PROCESSED_DIR = config["PROCESSED_DIR"]
FILES_LIMIT = config["FILES_LIMIT"]
N_PROCESS = config["N_PROCESS"]
META_PATH = config["META_PATH"]


@task
def check_if_repository_exists() -> None:
    """
    Function raises an exception if local data repository exists.

    :return: None
    """
    if exists(BASE_DATA_PATH):
        raise RepositoryExistsError("The local repository already exists!")


@task
def build_directory_tree(structure: list = DIRECTORY_TREE) -> None:
    """
    Function builds local directory tree defined in config.

    :return: None
    """
    logger = get_run_logger()
    for directory in structure:
        makedirs(directory, exist_ok=True)
        logger.info(f"Building dir: {directory}.")


@task(retries=3)
def request_gdc_service(
    fields: dict = FIELDS_CONFIG,
    filters: dict = FILTERS_CONFIG,
    n_records: int = FILES_LIMIT,
    output_file: str = GDC_RAW_RESPONSE_FILE,
) -> None:
    """
    Function requests GDC service to get files described in config file.

    :param fields:
    :param filters:
    :param n_records:
    :param output_file:
    :return: None
    """
    logger = get_run_logger()
    endpoint = "https://api.gdc.cancer.gov/files"

    fields = ",".join(fields)
    params = {"filters": filters, "fields": fields, "format": "TSV", "size": n_records}

    resp = requests.post(endpoint, json=params, timeout=1000)
    with open(output_file, "w", encoding="utf-8") as response_file:
        response_file.write(resp.text)

    logger.info("Exporting raw GDC response.")


@task
def build_sample_sheet(
    input_file: str = GDC_RAW_RESPONSE_FILE,
    output: str = SAMPLE_SHEET_FILE,
    sample_group_id: str = SAMPLE_GROUP_ID,
) -> None:
    """
    Function builds sample sheet based on GDC raw response.

    :param input_file:
    :param output:
    :param sample_group_id:
    :return: None
    """
    frame = pd.read_table(input_file)

    # fill nans in platform field
    frame.platform = frame.platform.fillna("RNA-Seq [platform - unknown]")

    # set index as case_id
    frame.index = frame["cases.0.case_id"]
    frame.index.name = ""

    # rename columns
    frame.columns = [name.split(".")[-1] if "." in name else name for name in frame.columns]

    # drop duplicated columns [sometimes from one case is multiple samples]
    frame = frame.loc[:, ~frame.columns.duplicated(keep="first")]

    # drop Illumina Human Methylation 27
    frame = frame[frame["platform"] != "Illumina Human Methylation 27"]

    # drop records without diagnosis OR origin tissue
    frame = frame[
        (~frame["primary_diagnosis"].isna()) | (~frame["tissue_or_organ_of_origin"].isna())
    ]

    # Remove redundant NOS prefix
    frame["tissue_or_organ_of_origin"] = frame["tissue_or_organ_of_origin"].str.replace(", NOS", "")

    # add <sample_group_id> field
    frame[sample_group_id] = (
        frame["sample_type"]
        + "_"
        + frame["tissue_or_organ_of_origin"]
        + "_"
        + frame["primary_diagnosis"]
    )

    frame.to_parquet(output)


@task
def prepare_samples_lists(
    sample_sheet_path: str = SAMPLE_SHEET_FILE,
    sample_group_id: str = SAMPLE_GROUP_ID,
    path_to_meta: str = META_PATH,
) -> None:

    collections = {}
    logger = get_run_logger()
    sample_sheet = pd.read_parquet(sample_sheet_path)

    for group_of_samples in sample_sheet[sample_group_id].unique():
        logger.info(f"Exporting SamplesCollection object per {group_of_samples}")

        # get cases in specific group_of_samples
        temp_sample_sheet = sample_sheet[sample_sheet[sample_group_id] == group_of_samples]
        single_collection = SamplesCollection(name=group_of_samples)

        for strategy in temp_sample_sheet["experimental_strategy"].unique():
            temp_sample_sheet_per_platform = temp_sample_sheet[
                temp_sample_sheet.experimental_strategy == strategy
            ]
            if strategy == "Methylation Array":
                single_collection.methylation_samples = set(temp_sample_sheet_per_platform.index)
            else:
                single_collection.expression_samples = set(temp_sample_sheet_per_platform.index)

        single_collection.extract_common()
        collections[group_of_samples] = single_collection

    with open(join(path_to_meta, "samples_collection.pkl"), "wb") as file:
        pickle.dump(collections, file)


@task
def build_manifest(
    strategy: str,
    path_to_meta: str = META_PATH,
    sample_sheet_path: str = SAMPLE_SHEET_FILE,
    sample_group_id: str = SAMPLE_GROUP_ID,
    manifests_base_path: str = INTERIM_BASE_PATH,
    max_samples: int = MAX_SAMPLES_PER_SAMPLE_GROUP,
    min_samples: int = MIN_SAMPLES_PER_SAMPLE_GROUP,
) -> Set[str]:
    """
    Function builds manifest files required by GDC downloading tool. These manifests are required by GDC-tool.
    One manifest is generated for one sample type in one specific directory. Moreover manifests are constrained by min and
    max number of samples.

    :param strategy:
    :param path_to_meta:
    :param sample_sheet_path:
    :param manifests_base_path:
    :param sample_group_id:
    :param max_samples:
    :param min_samples:
    :return final_list_of_samples:
    """

    np.random.seed(101)
    sample_sheet = pd.read_parquet(sample_sheet_path)
    sample_sheet = sample_sheet[sample_sheet.experimental_strategy == strategy]

    with open(join(path_to_meta, "samples_collection.pkl"), "rb") as file:
        collections = pickle.load(file)

    logger = get_run_logger()
    final_set_of_samples = set()
    endpoint = "https://api.gdc.cancer.gov/manifest/"

    for group_of_samples, collection in collections.items():
        temp_sample_sheet = sample_sheet[sample_sheet[sample_group_id] == group_of_samples]
        samples = collection.get_samples_list(strategy)

        if len(samples) < min_samples:  # condition for non-representative sample size

            logger.info(
                f"Skipping: {strategy} - {group_of_samples}, n < MIN_SAMPLES_PER_SAMPLE_GROUP"
            )
            continue

        if (
            len(samples) > max_samples and len(collection.get_common_samples_list) >= 50
        ):  # condition for sampling only from common samples group

            samples = np.random.choice(collection.get_common_samples_list, max_samples, False)
            logger.info(
                f"Complete sampling from: {strategy} - {group_of_samples} COMMON samples, n > MAX_SAMPLES_PER_SAMPLE_GROUP"
            )

        if (
            len(samples) > max_samples and 0 < len(collection.get_common_samples_list) < 50
        ):  # condition for sampling from common samples and non-common samples
            samples_p1 = collection.common_samples  # common samples
            n_to_sample = max_samples - len(
                samples_p1
            )  # number of additional samples to fill limit
            samples_2 = np.random.choice(
                list(set(samples).difference(set(samples_p1))), n_to_sample, False
            )  # sampling additional samples
            samples = samples_p1 | set(samples_2)
            logger.info(
                f"Partial sampling from: {strategy} - {group_of_samples} using {len(samples_p1)} COMMON samples and {len(samples_2)} non-COMMON samples, in summary n={len(samples)}, n > MAX_SAMPLES_PER_SAMPLE_GROUP"
            )

        if (
            len(samples) > max_samples and not collection.get_common_samples_list
        ):  # condition for sample only from non-COMMON samples (if common are not present)

            samples = np.random.choice(samples, max_samples, False)
            logger.info(
                f"Sampling from: {strategy} - {group_of_samples} using ONLY non-COMMON samples, n > MAX_SAMPLES_PER_SAMPLE_GROUP"
            )

        samples = list(samples)
        final_set_of_samples = final_set_of_samples | set(samples)
        files = temp_sample_sheet.loc[samples, "id"].tolist()

        # make dir for specific sample group
        makedirs(join(manifests_base_path, group_of_samples, strategy), exist_ok=True)

        # build manifest file
        params = {"ids": files}
        resp = requests.post(
            endpoint,
            data=json.dumps(params),
            headers={"Content-Type": "application/json"},
            timeout=1000,
        ).text

        with open(
            join(manifests_base_path, group_of_samples, strategy, "manifest.txt"),
            "w",
            encoding="utf-8",
        ) as manifest_file:
            manifest_file.write(resp)

        logger.info(
            f"Exporting manifest for: {group_of_samples}:{strategy} n samples: {len(samples)}"
        )

    return final_set_of_samples


@task
def update_sample_sheet(
    final_set_of_samples: Set[str], sample_sheet_path: str = SAMPLE_SHEET_FILE
) -> None:
    """
    Function updates sample sheet based on constrained manifest files.

    :param final_set_of_samples:
    :param sample_sheet_path:
    :return: None
    """
    logger = get_run_logger()
    sample_sheet = pd.read_parquet(sample_sheet_path)
    logger.info(f"Manifest size before update {sample_sheet.shape}")

    sample_sheet = sample_sheet[sample_sheet.index.isin(final_set_of_samples)]
    sample_sheet.to_parquet(sample_sheet_path)
    logger.info(f"Exporting updated manifest - shape {sample_sheet.shape}")


@task
def download(
    manifest_base_path: str = INTERIM_BASE_PATH, sample_sheet_path: str = SAMPLE_SHEET_FILE
) -> None:
    """
    Function downloads files using specific manifest file and GDC downloading tool.

    :param manifest_base_path:
    :param sample_sheet_path:
    :return: None
    """
    logger = get_run_logger()
    sample_sheet = pd.read_parquet(sample_sheet_path)

    for data_type in sample_sheet["experimental_strategy"].unique():
        manifests = glob(join(manifest_base_path, "*", f"{data_type}/manifest.txt"))

        for manifest in manifests:
            logger.info(f"Downloading: {manifest}")
            out_dir = str(Path(manifest).parent)

            command = [
                f"{GDC_TRANSFER_TOOL_EXECUTABLE}",
                "download",
                "-n",
                f"{N_PROCESS}",
                "--wait-time",
                "5",
                "-m",
                f"{manifest}",
                "-d",
                f"{out_dir}",
                "--retry-amount",
                "25",
            ]
            call(command)


@task
def build_met_frame(
    sample_sheet: str = SAMPLE_SHEET_FILE,
    base_path: str = INTERIM_BASE_PATH,
    out_dir: str = PROCESSED_DIR,
) -> None:
    """
    Function builds dataframes [Met] using data downloaded from GDC.

    :param ftype:
    :param sample_sheet:
    :param base_path:
    :param out_dir:
    :return: None
    """
    logger = get_run_logger()

    sample_groups = glob(join(base_path, "*/"))
    sample_groups = [str(Path(name).name) for name in sample_groups]
    sample_sheet = pd.read_parquet(sample_sheet)

    for sample_group in sample_groups:
        frame = []
        files_in = glob(join(base_path, sample_group, "Methylation Array", "*", "*level3betas.txt"))

        if files_in:
            for data_file in files_in:
                file_id = str(Path(data_file).parent.name)

                sample_id = sample_sheet[sample_sheet["id"] == file_id]["case_id"][0]
                sample = pd.read_table(data_file, header=None, index_col=0)

                sample.columns = [sample_id]
                sample.index.name = ""

                frame.append(sample)

            makedirs(join(out_dir, sample_group), exist_ok=True)
            frame = pd.concat(frame, axis=1)
            frame = frame.loc[:, ~frame.columns.duplicated(keep="first")]

            frame.to_parquet(join(out_dir, sample_group, "Methylation Array.parquet"), index=True)
            logger.info(f"Exporting Methylation frame for {sample_group}: {frame.shape}")


@task
def build_exp_frame(
    sample_sheet: str = SAMPLE_SHEET_FILE,
    base_path: str = INTERIM_BASE_PATH,
    out_dir: str = PROCESSED_DIR,
) -> None:
    """
    Function builds dataframe [Exp] using data downloaded from GDC.

    :param ftype:
    :param sample_sheet:
    :param base_path:
    :param out_dir:
    :return: None
    """
    logger = get_run_logger()

    sample_groups = glob(join(base_path, "*/"))
    sample_groups = [str(Path(name).name) for name in sample_groups]
    sample_sheet = pd.read_parquet(sample_sheet)

    for sample_group in sample_groups:
        frame = []
        files_in = glob(join(base_path, sample_group, "RNA-Seq", "*", "*_star_gene_counts.tsv"))

        if files_in:
            for data_file in files_in:
                file_id = str(Path(data_file).parent.name)

                sample_id = sample_sheet[sample_sheet["id"] == file_id]["case_id"][0]
                sample = pd.read_table(data_file, comment="#", low_memory=False)[
                    ["gene_name", "tpm_unstranded"]
                ]
                sample = sample.set_index("gene_name")
                sample = sample[~sample.index.isna()]
                sample = sample[~sample.index.duplicated(keep="first")]

                sample.columns = [sample_id]
                sample.index.name = ""

                frame.append(sample)

            makedirs(join(out_dir, sample_group), exist_ok=True)
            frame = pd.concat(frame, axis=1)
            frame = frame.loc[:, ~frame.columns.duplicated(keep="first")]

            frame.to_parquet(join(out_dir, sample_group, "RNA-Seq.parquet"), index=True)
            logger.info(f"Exporting Expression frame for {sample_group}: {frame.shape}")


@task
def metadata(final_dir: str = PROCESSED_DIR) -> None:
    """
    Function exports metadata file per each sample type. This file contains details about data type, number of samples,
    number of genes ad number of samples in specific data type repository.

    :param final_dir:
    :return: None
    """
    logger = get_run_logger()

    sample_groups = glob(join(final_dir, "*/"))
    sample_groups = [str(Path(name).name) for name in sample_groups]

    for sample_group in tqdm(sample_groups):
        met_file = join(final_dir, sample_group, "Methylation Array.parquet")
        exp_file = join(final_dir, sample_group, "RNA-Seq.parquet")

        if exists(met_file) and exists(exp_file):
            met_file = pd.read_parquet(met_file)
            exp_file = pd.read_parquet(exp_file)

            genes = set(exp_file.index)
            probes = set(met_file.index)

            exp_samples = set(exp_file.columns)
            met_samples = set(met_file.columns)
            common = exp_samples.intersection(met_samples)

            record = MetaRecord(
                sample_group,
                exp_file.shape,
                met_file.shape,
                genes,
                probes,
                exp_samples,
                met_samples,
                common,
            )

        elif exists(met_file):
            met_file = pd.read_parquet(met_file)
            probes = set(met_file.index)
            met_samples = set(met_file.columns)
            record = MetaRecord(
                sample_group,
                methylation_frame=met_file.shape,
                methylation_samples=met_samples,
                probes=probes,
            )

        elif exists(exp_file):
            exp_file = pd.read_parquet(exp_file)
            genes = set(exp_file.index)
            exp_samples = set(exp_file.columns)
            record = MetaRecord(
                sample_group,
                expression_frame=exp_file.shape,
                expression_samples=exp_samples,
                genes=genes,
            )

        else:
            record = MetaRecord(sample_group)

        with open(join(final_dir, sample_group, "metadata"), "wb") as meta_file:
            pickle.dump(record.record, meta_file)

        logger.info(f"Exporting metadata for {sample_group}")


@task
def clean_sample_sheet(
    final_dir: str = PROCESSED_DIR, sample_sheet_path: str = SAMPLE_SHEET_FILE
) -> None:
    """
    Function cleans sample sheet due to possible connections issue when data downloading. It means that if error occurs
    and certain sample is not present in meta file it will be removed from sample sheet.

    :param final_dir:
    :param sample_sheet_path:
    :return: None
    """
    logger = get_run_logger()

    meta_files = glob(join(final_dir, "*", "metadata"))
    sample_sheet = pd.read_parquet(sample_sheet_path)

    exp_samples = set()
    met_samples = set()

    for file in meta_files:
        meta = pd.read_pickle(file)
        exp_samples_, met_samples_ = meta["expressionSamples"], meta["methylationSamples"]
        exp_samples = exp_samples | exp_samples_
        met_samples = met_samples | met_samples_

    exp_sample_sheet = sample_sheet[
        (sample_sheet.index.isin(exp_samples) & (sample_sheet.experimental_strategy == "RNA-Seq"))
    ]

    met_sample_sheet = sample_sheet[
        (
            sample_sheet.index.isin(met_samples)
            & (sample_sheet.experimental_strategy == "Methylation Array")
        )
    ]

    cleaned_sample_sheet = pd.concat((exp_sample_sheet, met_sample_sheet))
    cleaned_sample_sheet.to_parquet(sample_sheet_path)

    logger.info(
        f"Exporting final sample sheet {cleaned_sample_sheet}, initial shape was {sample_sheet.shape}"
    )


@task
def global_metadata(
    final_dir: str = PROCESSED_DIR,
    min_samples: int = MIN_COMMON_SAMPLES,
    metadata_global_path: str = METADATA_GLOBAL_FILE,
) -> None:
    """
    Function builds global metadata file for all sample types. It contains information about which sample types
    have Exp and/or Met datasets additionally it contains information about datasets comprising common samples between Met and
    Exp.

    :param final_dir:
    :param min_samples:
    :param metadata_global_path:
    :return: None
    """
    logger = get_run_logger()
    sample_groups = glob(join(final_dir, "*/"))

    exp_files_present = []
    met_files_present = []
    met_exp_files_present = []
    met_exp_files_with_common_samples_present = []

    for sample_group in tqdm(sample_groups):
        local_metadata = pd.read_pickle(join(sample_group, "metadata"))
        sample_group = Path(sample_group).name

        if local_metadata["expressionFrame"] and local_metadata["methylationFrame"]:
            met_exp_files_present.append(sample_group)

        if local_metadata["expressionFrame"]:
            exp_files_present.append(sample_group)

        if local_metadata["methylationFrame"]:
            met_files_present.append(sample_group)

        if local_metadata["commonBetween"]:
            if len(local_metadata["commonBetween"]) > min_samples:
                met_exp_files_with_common_samples_present.append(sample_group)

    record = GlobalMetaRecord(
        len(sample_groups),
        exp_files_present,
        met_files_present,
        met_exp_files_present,
        met_exp_files_with_common_samples_present,
    )

    with open(metadata_global_path, "wb") as meta_file:
        pickle.dump(record.record, meta_file)

    logger.info("Exporting global metadata for whole repository")


@task
def create_repo_summary(
    output_file: str = SUMMARY_METAFILE,
    sample_sheet_path: str = SAMPLE_SHEET_FILE,
    metadata_path: str = METADATA_GLOBAL_FILE,
) -> None:
    """
    Function builds repo summary object which contains descriptive data about local data repository.
    E.g., number of samples, used technology etc.

    :param output_file:
    :param sample_sheet_path:
    :param metadata_path:
    :return: None
    """
    logger = get_run_logger()
    sample_sheet = pd.read_parquet(sample_sheet_path)
    sample_sheet = sample_sheet[
        ["primary_diagnosis", "tissue_or_organ_of_origin", "sample_type", "platform"]
    ]

    metafile = pd.read_pickle(metadata_path)

    last_update = metafile["creationDate"]
    number_of_groups = metafile["Number_of_sample_types"]

    number_of_samples = sample_sheet.shape[0]
    primary_diagnosis = sample_sheet["primary_diagnosis"].value_counts()
    tissue_origin = sample_sheet["tissue_or_organ_of_origin"].value_counts()
    sample_type = sample_sheet["sample_type"].value_counts()
    exp_strategy = sample_sheet["platform"].value_counts()

    record = RepositorySummary(
        last_update,
        number_of_groups,
        number_of_samples,
        primary_diagnosis,
        tissue_origin,
        sample_type,
        exp_strategy,
    )

    with open(output_file, "wb") as meta_file:
        pickle.dump(record.record, meta_file)

    logger.info("Exporting summary meta file for local repository")


@flow(name="Building data repository")
def run():
    check_if_repository_exists()
    build_directory_tree()
    request_gdc_service()

    build_sample_sheet()
    prepare_samples_lists()

    samples_set_Met = build_manifest("Methylation Array")
    samples_set_Exp = build_manifest("RNA-Seq")
    update_sample_sheet(samples_set_Exp | samples_set_Met)

    download()
    build_met_frame()
    build_exp_frame()

    metadata()
    clean_sample_sheet()
    global_metadata()
    create_repo_summary()


run()
