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
from src.exceptions import RepositoryExistsError
from src.records import GlobalMetaRecord, MetaRecord, RepositorySummary
from src.utils import load_config
from tqdm import tqdm

np.random.seed(101)
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


@task
def check_if_repository_exists() -> None:
    if exists(BASE_DATA_PATH):
        raise RepositoryExistsError("The local repository already exists!")


@task
def build_directory_tree() -> None:
    logger = get_run_logger()
    for directory in DIRECTORY_TREE:
        makedirs(directory)
        logger.info(f"Building dir: {directory}.")


@task(retries=3)
def request_gdc_service(
    fields: dict = FIELDS_CONFIG,
    filters: dict = FILTERS_CONFIG,
    n_records: int = FILES_LIMIT,
    output_file: str = GDC_RAW_RESPONSE_FILE,
) -> None:
    """
    Function to request GDC, as response it returns df with files.
    Requested number of records, fields, and filters are declared in config.py file.
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
    Function build sample sheet based on raw GDC response.
    """
    frame = pd.read_table(input_file)

    # fill nans in platform field
    frame.platform = frame.platform.fillna("RNA-seq [platform - unknown]")

    # set index as case id
    frame = frame.set_index("cases.0.case_id")
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
def build_manifest(
    sample_sheet_path: str = SAMPLE_SHEET_FILE,
    manifest_base_path: str = INTERIM_BASE_PATH,
    sample_group_id: str = SAMPLE_GROUP_ID,
    max_samples: int = MAX_SAMPLES_PER_SAMPLE_GROUP,
    min_samples: int = MIN_SAMPLES_PER_SAMPLE_GROUP,
) -> List[str]:
    """
    Function to build manifest for each specific group_of_samples present in sample_group_id field.
    > Only sample groups containing > MIN_SAMPLES_PER_SAMPLE_GROUP are processed to further steps.
    > If number of samples > MAX_SAMPLES_PER_SAMPLE_GROUP, random subset
    [equal to MAX_SAMPLES_PER_SAMPLE_GROUP]  is used.
    Manifest files are exported to location: <base_path / sample group / file_type [Met / Exp] / manifest.txt>.
    Manifest file is an input for GDC download tool.
    """

    logger = get_run_logger()
    sample_sheet = pd.read_parquet(sample_sheet_path)
    final_list_of_samples = []

    endpoint = "https://api.gdc.cancer.gov/manifest/"
    end_file = {"RNA-Seq": "Exp", "Methylation Array": "Met"}

    for strategy in sample_sheet["experimental_strategy"].unique():
        temporary_sample_sheet = sample_sheet[sample_sheet["experimental_strategy"] == strategy]

        for group_of_samples in temporary_sample_sheet[sample_group_id].unique():

            # get cases in specific group_of_samples
            files = temporary_sample_sheet[
                temporary_sample_sheet[sample_group_id] == group_of_samples
            ]
            files = files["id"].tolist()

            if len(files) < min_samples:
                logger.info(
                    f"Skipping: {strategy} - {group_of_samples}, n < MIN_SAMPLES_PER_SAMPLE_GROUP"
                )
                continue

            if len(files) > max_samples:
                logger.info(
                    f"Sampling from: {strategy} - {group_of_samples}, n > MAX_SAMPLES_PER_SAMPLE_GROUP"
                )
                files = list(np.random.choice(files, max_samples, False))

            final_list_of_samples.extend(files)

            # make dir for specific sample group
            makedirs(join(manifest_base_path, group_of_samples, end_file[strategy]), exist_ok=True)

            # build manifest file
            params = {"ids": files}
            resp = requests.post(
                endpoint,
                data=json.dumps(params),
                headers={"Content-Type": "application/json"},
                timeout=1000,
            ).text

            with open(
                join(manifest_base_path, group_of_samples, end_file[strategy], "manifest.txt"),
                "w",
                encoding="utf-8",
            ) as manifest_file:
                manifest_file.write(resp)

            logger.info(
                f"Exporting manifest for: {group_of_samples}:{end_file[strategy]} n samples: {len(files)}"
            )

    return final_list_of_samples


@task
def update_sample_sheet(
    final_list_of_samples: List[str], sample_sheet_path: str = SAMPLE_SHEET_FILE
) -> None:
    logger = get_run_logger()
    sample_sheet = pd.read_parquet(sample_sheet_path)

    sample_sheet = sample_sheet[sample_sheet["id"].isin(final_list_of_samples)]
    sample_sheet.to_parquet(sample_sheet_path)
    logger.info("Exporting updated manifest")


@task
def download(manifest_base_path: str = INTERIM_BASE_PATH) -> None:
    """
    Function to download methylation files specified in manifest file.
    """
    logger = get_run_logger()
    for data_type in ["Met", "Exp"]:
        manifests = glob(join(manifest_base_path, "*", f"{data_type}/manifest.txt"))

        for manifest in manifests:
            logger.info(f"Downloading: {manifest}")
            out_dir = str(Path(manifest).parent)

            command = [
                f"{GDC_TRANSFER_TOOL_EXECUTABLE}",
                "download",
                "-n",
                f"{N_PROCESS}",
                "-m",
                f"{manifest}",
                "-d",
                f"{out_dir}",
                "--retry-amount",
                "10",
            ]
            call(command)


@task
def build_frames(
    ftype: str,
    sample_sheet: str = SAMPLE_SHEET_FILE,
    base_path: str = INTERIM_BASE_PATH,
    out_dir: str = PROCESSED_DIR,
) -> None:
    """
    Function to concatenate methylation files into dataframe.
    Final dataframe is exported as parquet file to: <out_dir / sample_group / [ftype].parquet>.
    ftype: str = Met|Exp
    """
    logger = get_run_logger()

    sample_groups = glob(join(base_path, "*/"))
    sample_groups = [str(Path(name).name) for name in sample_groups]
    sample_sheet = pd.read_parquet(sample_sheet)

    for sample_group in sample_groups:
        frame = []

        if ftype == "Met":
            files_in = glob(join(base_path, sample_group, ftype, "*/", "*level3betas.txt"))
        else:
            files_in = glob(join(base_path, sample_group, ftype, "*/", "*_star_gene_counts.tsv"))

        if files_in:
            for data_file in files_in:
                file_id = str(Path(data_file).parent.name)

                sample_id = sample_sheet[sample_sheet["id"] == file_id].index[0]

                if ftype == "Met":
                    sample = pd.read_table(data_file, header=None, index_col=0)

                else:
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

            frame.to_parquet(join(out_dir, sample_group, f"{ftype}.parquet"), index=True)
            logger.info(f"Exporting {ftype} frame for {sample_group}: {frame.shape}")


@task
def metadata(final_dir: str = PROCESSED_DIR) -> None:
    """
    Function to export metadata file per sample group, it contains information about creation time, frames dimensions
    and samples common between Met and Exp files.
    """
    logger = get_run_logger()

    sample_groups = glob(join(final_dir, "*/"))
    sample_groups = [str(Path(name).name) for name in sample_groups]

    for sample_group in tqdm(sample_groups):
        met_file = join(final_dir, sample_group, "Met.parquet")
        exp_file = join(final_dir, sample_group, "Exp.parquet")

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
def global_metadata(
    final_dir: str = PROCESSED_DIR,
    min_samples: int = MIN_COMMON_SAMPLES,
    metadata_global_path: str = METADATA_GLOBAL_FILE,
) -> None:
    """
    Function to export global metafile it contains general information about whole repository.
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
):
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
    samples = build_manifest()
    update_sample_sheet(samples)

    download()
    build_frames("Exp")
    build_frames("Met")

    metadata()
    global_metadata()
    create_repo_summary()


run()
