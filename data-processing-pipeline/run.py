import json
import pickle
from glob import glob
from os import makedirs
from os.path import exists, join
from pathlib import Path
from subprocess import call
from typing import List

import numpy as np
import pandas as pd
import requests
from prefect import flow, get_run_logger, task
from src.collector import SamplesCollector
from src.exceptions import NonUniqueIndex, RepositoryExistsError
from src.records import GlobalMetaRecord, MetaRecord, RepositorySummary
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

    # set index as file id
    frame = frame.set_index("id")
    frame.index.name = ""

    if len(frame.index) != len(set(frame.index)):
        raise NonUniqueIndex("Sample sheet index are not unique.")

    # fill nans in platform field
    frame.platform = frame.platform.fillna("RNA-Seq [platform - unknown]")

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
def prepare_samples_collections(
    sample_sheet_path: str = SAMPLE_SHEET_FILE,
    sample_group_id: str = SAMPLE_GROUP_ID,
    path_to_meta: str = META_PATH,
) -> None:

    collections = {}
    logger = get_run_logger()
    np.random.seed(101)

    sample_sheet = pd.read_parquet(sample_sheet_path)
    exp_sample_sheet = sample_sheet[sample_sheet.experimental_strategy == "RNA-Seq"]
    met_sample_sheet = sample_sheet[sample_sheet.experimental_strategy == "Methylation Array"]

    for group_of_samples in sample_sheet[sample_group_id].unique():
        logger.info(f"Exporting SamplesCollection object per {group_of_samples}")

        exp_samples = (
            exp_sample_sheet[exp_sample_sheet[sample_group_id] == group_of_samples]["case_id"]
            .drop_duplicates(keep="first")
            .tolist()
        )

        met_samples = (
            met_sample_sheet[met_sample_sheet[sample_group_id] == group_of_samples]["case_id"]
            .drop_duplicates(keep="first")
            .tolist()
        )

        common_samples = list(set(exp_samples).intersection(set(met_samples)))
        collection = SamplesCollector(
            name=sample_group_id,
            methylation_samples=met_samples,
            expression_samples=exp_samples,
            common_samples=common_samples,
            max_samples=MAX_SAMPLES_PER_SAMPLE_GROUP,
            min_samples=MIN_SAMPLES_PER_SAMPLE_GROUP,
        )

        collections[group_of_samples] = collection

    with open(join(path_to_meta, "samples_collection.pkl"), "wb") as file:
        pickle.dump(collections, file)


@task
def build_manifest(
    strategy: str,
    path_to_meta: str = META_PATH,
    sample_group_id: str = SAMPLE_GROUP_ID,
    sample_sheet_path: str = SAMPLE_SHEET_FILE,
    manifests_base_path: str = INTERIM_BASE_PATH,
    endpoint="https://api.gdc.cancer.gov/manifest/",
) -> List[str]:
    """
    Function builds manifest files required by GDC downloading tool.

    :param strategy:
    :param path_to_meta:
    :param sample_group_id:
    :param sample_sheet_path:
    :param manifests_base_path:
    :param endpoint:
    :return final_list_of_samples:
    """

    sample_sheet = pd.read_parquet(sample_sheet_path)
    with open(join(path_to_meta, "samples_collection.pkl"), "rb") as file:
        collections = pickle.load(file)

    logger = get_run_logger()
    final_set_of_files = []

    for group_of_samples, collection in collections.items():
        temp_sample_sheet = sample_sheet[
            (sample_sheet.experimental_strategy == strategy)
            & (sample_sheet[sample_group_id] == group_of_samples)
        ]

        samples = collection.get_samples_list(strategy)
        files = temp_sample_sheet[temp_sample_sheet.case_id.isin(samples)].index.tolist()
        final_set_of_files.extend(files)

        if len(files) != len(set(files)):
            raise NonUniqueIndex(f"Non unique files ids for {group_of_samples}-{strategy}")

        if len(files) == 0:
            continue

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

    return final_set_of_files


@task
def update_sample_sheet(
    final_set_of_files: List[str], sample_sheet_path: str = SAMPLE_SHEET_FILE
) -> None:
    """
    Function updates sample sheet based on constrained manifest files.

    :param final_set_of_files:
    :param sample_sheet_path:
    :return: None
    """
    logger = get_run_logger()
    sample_sheet = pd.read_parquet(sample_sheet_path)
    logger.info(f"Manifest shape before removing unused files {sample_sheet.shape}")

    sample_sheet = sample_sheet.loc[final_set_of_files, :]
    sample_sheet.to_parquet(sample_sheet_path)
    logger.info(f"Manifest shape after removing unused files {sample_sheet.shape}")


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

    for strategy in sample_sheet["experimental_strategy"].unique():
        manifests = glob(join(manifest_base_path, "*", strategy, "manifest.txt"))

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
    interim_files_path: str = INTERIM_BASE_PATH,
    processed_dir: str = PROCESSED_DIR,
) -> None:
    """
    Function builds data frames [Met] using interim data downloaded from GDC.

    :param sample_sheet:
    :param interim_files_path:
    :param processed_dir:
    :return: None
    """
    logger = get_run_logger()

    sample_groups = glob(join(interim_files_path, "*/"))
    sample_groups = [Path(name).name for name in sample_groups]
    sample_sheet = pd.read_parquet(sample_sheet)

    for sample_group in sample_groups:
        frame = []
        files_in_sample_group = glob(
            join(interim_files_path, sample_group, "Methylation Array/", "*/", "*level3betas.txt")
        )

        if files_in_sample_group:
            for data_file in files_in_sample_group:
                file_id = str(Path(data_file).parent.name)

                sample_id = sample_sheet.loc[file_id, "case_id"]
                sample = pd.read_table(data_file, header=None, index_col=0)

                sample.columns = [sample_id]
                sample.index.name = ""

                frame.append(sample)

            makedirs(join(processed_dir, sample_group), exist_ok=True)
            frame = pd.concat(frame, axis=1)
            frame = frame.loc[:, ~frame.columns.duplicated(keep="first")]

            frame.to_parquet(
                join(processed_dir, sample_group, "Methylation Array.parquet"), index=True
            )
            logger.info(f"Exporting Methylation frame for {sample_group}: {frame.shape}")


@task
def build_exp_frame(
    sample_sheet: str = SAMPLE_SHEET_FILE,
    interim_files_path: str = INTERIM_BASE_PATH,
    processed_dir: str = PROCESSED_DIR,
) -> None:
    """
    Function builds dataframe [Exp] using data downloaded from GDC.

    :param sample_sheet:
    :param interim_files_path:
    :param processed_dir:
    :return: None
    """
    logger = get_run_logger()

    sample_groups = glob(join(interim_files_path, "*/"))
    sample_groups = [Path(name).name for name in sample_groups]
    sample_sheet = pd.read_parquet(sample_sheet)

    for sample_group in sample_groups:
        frame = []
        files_in_sample_group = glob(
            join(interim_files_path, sample_group, "RNA-Seq/", "*/", "*_star_gene_counts.tsv")
        )

        if files_in_sample_group:
            for data_file in files_in_sample_group:
                file_id = str(Path(data_file).parent.name)

                sample_id = sample_sheet.loc[file_id, "case_id"]
                sample = pd.read_table(data_file, comment="#", low_memory=False)[
                    ["gene_name", "tpm_unstranded"]
                ]
                sample = sample.set_index("gene_name")
                sample = sample[~sample.index.isna()]
                sample = sample[~sample.index.duplicated(keep="first")]

                sample.columns = [sample_id]
                sample.index.name = ""

                frame.append(sample)

            makedirs(join(processed_dir, sample_group), exist_ok=True)
            frame = pd.concat(frame, axis=1)
            frame = frame.loc[:, ~frame.columns.duplicated(keep="first")]

            frame.to_parquet(join(processed_dir, sample_group, "RNA-Seq.parquet"), index=True)
            logger.info(f"Exporting Expression frame for {sample_group}: {frame.shape}")


@task
def metadata(processed_dir: str = PROCESSED_DIR) -> None:
    """
    Function exports metadata file per each sample type.
    This file allows fast access to information about single unit (sample type) in local data repository..

    :param processed_dir:
    :return: None
    """
    logger = get_run_logger()

    sample_groups = glob(join(processed_dir, "*/"))
    sample_groups = [str(Path(name).name) for name in sample_groups]

    for sample_group in tqdm(sample_groups):
        met_file = join(processed_dir, sample_group, "Methylation Array.parquet")
        exp_file = join(processed_dir, sample_group, "RNA-Seq.parquet")

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

        with open(join(processed_dir, sample_group, "metadata.pkl"), "wb") as meta_file:
            pickle.dump(record.record, meta_file)

        logger.info(f"Exporting metadata for {sample_group}")


@task
def clean_sample_sheet(
    processed_dir: str = PROCESSED_DIR, sample_sheet_path: str = SAMPLE_SHEET_FILE
) -> None:
    """
    Function cleans sample sheet due to possible connections issue when data downloading.

    :param processed_dir:
    :param sample_sheet_path:
    :return: None
    """
    logger = get_run_logger()

    meta_files = glob(join(processed_dir, "*", "metadata.pkl"))
    sample_sheet = pd.read_parquet(sample_sheet_path)

    exp_samples = set()
    met_samples = set()

    for file in meta_files:
        meta = pd.read_pickle(file)
        exp_samples_, met_samples_ = meta["expressionSamples"], meta["methylationSamples"]
        exp_samples = exp_samples | exp_samples_
        met_samples = met_samples | met_samples_

    exp_sample_sheet = sample_sheet[
        (sample_sheet.case_id.isin(exp_samples) & (sample_sheet.experimental_strategy == "RNA-Seq"))
    ]

    met_sample_sheet = sample_sheet[
        (
            sample_sheet.case_id.isin(met_samples)
            & (sample_sheet.experimental_strategy == "Methylation Array")
        )
    ]

    cleaned_sample_sheet = pd.concat((exp_sample_sheet, met_sample_sheet))
    cleaned_sample_sheet.to_parquet(sample_sheet_path)

    logger.info(
        f"Final sample sheet shape is {cleaned_sample_sheet.shape}, initial shape was {sample_sheet.shape}."
    )


@task
def global_metadata(
    processed_dir: str = PROCESSED_DIR,
    min_samples: int = MIN_COMMON_SAMPLES,
    metadata_global_path: str = METADATA_GLOBAL_FILE,
) -> None:
    """
    Function builds global metadata file for all sample types.
    This file allows fast and spimple access to global information about local repository.

    :param processed_dir:
    :param min_samples:
    :param metadata_global_path:
    :return: None
    """
    logger = get_run_logger()
    sample_groups = glob(join(processed_dir, "*/"))

    exp_files_present = []
    met_files_present = []
    met_exp_files_present = []
    met_exp_files_with_common_samples_present = []

    for sample_group in tqdm(sample_groups):
        local_metadata = pd.read_pickle(join(sample_group, "metadata.pkl"))
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

    logger.info("Exporting global metadata file for current local repository.")


@task
def create_repo_summary(
    output_file: str = SUMMARY_METAFILE,
    sample_sheet_path: str = SAMPLE_SHEET_FILE,
    metadata_path: str = METADATA_GLOBAL_FILE,
) -> None:
    """
    Function builds repo summary object which contains descriptive details about local data repository.

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
    prepare_samples_collections()

    met_files = build_manifest("Methylation Array")
    exp_files = build_manifest("RNA-Seq")
    update_sample_sheet([*met_files, *exp_files])

    download()
    build_met_frame()
    build_exp_frame()

    metadata()
    clean_sample_sheet()
    global_metadata()
    create_repo_summary()


run()
