import json
import pickle
from datetime import datetime
from glob import glob
from os import makedirs
from os.path import exists, join
from pathlib import Path
from subprocess import call

import numpy as np
import pandas as pd
import requests
from prefect import flow, get_run_logger, task
from src.exceptions import RepositoryExistsError
from src.utils import load_config
from tqdm import tqdm

np.random.seed(101)
config = load_config()

GDC_TRANSFER_TOOL_EXECUTABLE = config["GDC_TRANSFER_TOOL_EXECUTABLE"]
MIN_SAMPLES_PER_SAMPLE_GROUP = config["MIN_SAMPLES_PER_SAMPLE_GROUP"]
MAX_SAMPLES_PER_SAMPLE_GROUP = config["MAX_SAMPLES_PER_SAMPLE_GROUP"]
GDC_RAW_RESPONSE_FILE = config["GDC_RAW_RESPONSE_FILE"]
METADATA_GLOBAL_FILE = config["METADATA_GLOBAL_FILE"]
MANIFEST_BASE_PATH = config["MANIFEST_BASE_PATH"]
MIN_COMMON_SAMPLES = config["MIN_COMMON_SAMPLES"]
SAMPLE_SHEET_FILE = config["SAMPLE_SHEET_FILE"]
SUMMARY_METAFILE = config["SUMMARY_METAFILE"]
SAMPLE_GROUP_ID = config["SAMPLE_GROUP_ID"]
FILTERS_CONFIG = config["FILTERS_CONFIG"]
DIRECTORY_TREE = config["DIRECTORY_TREE"]
FIELDS_CONFIG = config["FIELDS_CONFIG"]
PROCESSED_DIR = config["PROCESSED_DIR"]
FILES_LIMIT = config["FILES_LIMIT"]
N_PROCESS = config["N_PROCESS"]


@task
def check_if_repository_exists() -> None:
    if exists("data/"):
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

    resp = requests.post(endpoint, json=params)
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

    # drop records without diagnosis or origin tissue
    frame = frame[
        (~frame["primary_diagnosis"].isna()) & (~frame["tissue_or_organ_of_origin"].isna())
    ]

    # Remove redundant NOS prefix
    frame["tissue_or_organ_of_origin"] = frame["tissue_or_organ_of_origin"].str.replace(", NOS", "")

    # add <sample_group_id> field
    frame[sample_group_id] = (
        frame["tissue_type"]
        + "_"
        + frame["tissue_or_organ_of_origin"]
        + "_"
        + frame["primary_diagnosis"]
    )

    frame.to_parquet(output)


@task(retries=3)
def build_manifest(
    sample_sheet: str = SAMPLE_SHEET_FILE,
    base_path: str = MANIFEST_BASE_PATH,
    sample_group_id: str = SAMPLE_GROUP_ID,
    max_samples: int = MAX_SAMPLES_PER_SAMPLE_GROUP,
    min_samples: int = MIN_SAMPLES_PER_SAMPLE_GROUP,
) -> None:
    """
    Function to build manifest for each specific group_of_samples present in sample_group_id field.
    Only sample groups containing > min_samples_per_sample_group are processed to further steps.
    Manifest files are exported to location: <base_path / sample group / file_type [Met / Exp] / manifest.txt>.
    Manifest file is an input for GDC download tool.
    """

    logger = get_run_logger()
    sample_sheet = pd.read_parquet(
        sample_sheet, columns=["id", "experimental_strategy", sample_group_id]
    )
    endpoint = "https://api.gdc.cancer.gov/manifest/"

    for group_of_samples in sample_sheet[sample_group_id].unique():

        # get cases in specific group_of_samples
        partial_sample_sheet = sample_sheet[sample_sheet[sample_group_id] == group_of_samples]

        # get RNA seq files ids
        expression_files = partial_sample_sheet[
            partial_sample_sheet["experimental_strategy"] == "RNA-Seq"
        ]
        expression_files = expression_files["id"].tolist()
        if len(expression_files) < min_samples:
            expression_files = []

        if len(expression_files) > max_samples:
            expression_files = np.random.choice(expression_files, max_samples)

        # get methylation files ids
        methylation_files = partial_sample_sheet[
            partial_sample_sheet["experimental_strategy"] == "Methylation Array"
        ]
        methylation_files = methylation_files["id"].tolist()
        if len(methylation_files) < min_samples:
            methylation_files = []

        if len(methylation_files) > max_samples:
            methylation_files = np.random.choice(methylation_files, max_samples)

        # prepare data to request
        to_request = zip(["Exp", "Met"], [expression_files, methylation_files])

        for file_type, files in to_request:
            if files:
                # make dir for specific sample group
                makedirs(join(base_path, group_of_samples, file_type), exist_ok=True)

                # build manifest file
                params = {"ids": files}
                resp = requests.post(
                    endpoint,
                    data=json.dumps(params),
                    headers={"Content-Type": "application/json"},
                )
                resp = resp.text

                with open(
                    join(base_path, group_of_samples, file_type, "manifest.txt"),
                    "w",
                    encoding="utf-8",
                ) as manifest_file:
                    manifest_file.write(resp)

                logger.info(
                    f"Exporting manifest for: {group_of_samples}:{file_type} n samples: {len(files)}"
                )


@task()
def download_methylation_files(base_path: str = MANIFEST_BASE_PATH) -> None:
    """
    Function to download methylation files specified in manifest file.
    """
    logger = get_run_logger()
    manifests_met = glob(join(base_path, "*", "Met/manifest.txt"))

    for manifest in manifests_met:
        logger.info(f"Downloading: {manifest}")
        out_dir = str(Path(manifest).parent)

        command = (
            f"{GDC_TRANSFER_TOOL_EXECUTABLE} download -n {N_PROCESS} -m '{manifest}' -d '{out_dir}' --retry"
            f"-amount 10 "
        )
        call(command, shell=True)


@task()
def download_expression_files(base_path: str = MANIFEST_BASE_PATH) -> None:
    """
    Function to download expression files specified in manifest file.
    """
    logger = get_run_logger()
    manifests_exp = glob(join(base_path, "*", "Exp/manifest.txt"))

    for manifest in manifests_exp:
        logger.info(f"Downloading: {manifest}")
        out_dir = str(Path(manifest).parent)

        command = (
            f"{GDC_TRANSFER_TOOL_EXECUTABLE} download -n {N_PROCESS} -m '{manifest}' -d '{out_dir}' --retry"
            f"-amount 10 "
        )
        call(command, shell=True)


@task
def build_frames(
    ftype: str,
    sample_sheet: str = SAMPLE_SHEET_FILE,
    base_path: str = MANIFEST_BASE_PATH,
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
                    sample = pd.read_table(data_file, comment="#")[["gene_name", "tpm_unstranded"]]
                    sample = sample.set_index("gene_name")
                    sample = sample[~sample.index.isna()]

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

            meta = {
                "SampleGroup": sample_group,
                "creationDate": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "expressionFrame": exp_file.shape,
                "methylationFrame": met_file.shape,
                "genes": genes,
                "probes": probes,
                "expressionSamples": exp_samples,
                "methylationSamples": met_samples,
                "commonBetween": common,
            }

        elif exists(met_file):
            met_file = pd.read_parquet(met_file)
            probes = set(met_file.index)
            met_samples = set(met_file.columns)

            meta = {
                "SampleGroup": sample_group,
                "creationDate": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "expressionFrame": "",
                "methylationFrame": met_file.shape,
                "genes": "",
                "probes": probes,
                "expressionSamples": "",
                "methylationSamples": met_samples,
                "commonBetween": "",
            }

        elif exists(exp_file):
            exp_file = pd.read_parquet(exp_file)
            genes = set(exp_file.index)
            exp_samples = set(exp_file.columns)
            meta = {
                "SampleGroup": sample_group,
                "creationDate": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "expressionFrame": exp_file.shape,
                "methylationFrame": "",
                "genes": genes,
                "probes": "",
                "expressionSamples": exp_samples,
                "methylationSamples": "",
                "commonBetween": "",
            }

        else:
            meta = {
                "SampleGroup": sample_group,
                "creationDate": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "expressionFrame": "",
                "methylationFrame": "",
                "genes": "",
                "probes": "",
                "expressionSamples": "",
                "methylationSamples": "",
                "commonBetween": "",
            }

        with open(join(final_dir, sample_group, "metadata"), "wb") as meta_file:
            pickle.dump(meta, meta_file)

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

    meta = {
        "Date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "Number_of_sample_types": len(sample_groups),
        "Expression_files_present": exp_files_present,
        "Methylation_files_present": met_files_present,
        "Methylation_expression_files_present": met_exp_files_present,
        "Methylation_expression_files_with_common_samples_present": met_exp_files_with_common_samples_present,
    }

    with open(metadata_global_path, "wb") as meta_file:
        pickle.dump(meta, meta_file)

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

    last_update = metafile["Date"]
    number_of_groups = metafile["Number_of_sample_types"]

    number_of_samples = sample_sheet.shape[0]
    primary_diagnosis = sample_sheet["primary_diagnosis"].value_counts()
    tissue_origin = sample_sheet["tissue_or_organ_of_origin"].value_counts()
    sample_type = sample_sheet["sample_type"].value_counts()
    exp_strategy = sample_sheet["platform"].value_counts()

    meta = {
        "last_update": last_update,
        "number_of_samples_groups": number_of_groups,
        "number_of_samples": number_of_samples,
        "primary_diagnosis_cnt": primary_diagnosis,
        "tissue_origin_cnt": tissue_origin,
        "sample_type_cnt": sample_type,
        "exp_strategy_cnt": exp_strategy,
    }

    with open(output_file, "wb") as meta_file:
        pickle.dump(meta, meta_file)

    logger.info("Exporting summary meta file for local repository")


@flow(name="Building data repository")
def run():
    check_if_repository_exists()
    build_directory_tree()
    request_gdc_service()

    build_sample_sheet()
    build_manifest()

    download_methylation_files()
    download_expression_files()

    build_frames("Exp")
    build_frames("Met")

    metadata()
    global_metadata()

    create_repo_summary()


run()
