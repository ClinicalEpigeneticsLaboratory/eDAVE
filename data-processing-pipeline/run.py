import json
import pickle
from os import makedirs
from os.path import exists
from os.path import join
from subprocess import call
from datetime import datetime

from prefect import flow, task, get_run_logger
from pathlib import Path
from glob import glob
from tqdm import tqdm
import pandas as pd
import requests

from config import files_limit
from config import fields_config
from config import filters_config
from config import directory_tree
from config import gdc_transfer_tool_executable
from config import n_process
from config import gdc_raw_response_file
from config import sample_sheet_file
from config import min_samples_per_sample_group
from config import manifest_base_path
from config import processed_dir
from config import min_common_samples
from config import metadata_global_file
from config import summary_metafile


@task
def build_directory_tree() -> None:
    logger = get_run_logger()
    for directory in directory_tree:
        makedirs(directory, exist_ok=True)
        logger.info(f"Building dir: {directory}.")


@task(retries=3)
def request_GDC(
    fields: dict = fields_config,
    filters: dict = filters_config,
    n_records: int = files_limit,
    output_file: str = gdc_raw_response_file,
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
    with open(output_file, "w") as file:
        file.write(resp.text)

    logger.info("Exporting raw GDC response.")


@task
def build_sample_sheet(
    input_file: str = gdc_raw_response_file, output: str = sample_sheet_file
) -> None:
    """
    Function build sample sheet based on raw GDC response.
    """
    df = pd.read_table(input_file)

    # fill nans in platform field
    df.platform = df.platform.fillna("RNA-seq [platform - unknown]")

    # drop 27K records
    df = df[df["platform"] != "Illumina Human Methylation 27"]

    # set index as case id
    df = df.set_index("cases.0.case_id")
    df.index.name = ""

    # rename columns
    df.columns = [name.split(".")[-1] if "." in name else name for name in df.columns]

    # drop duplicated columns [sometimes from one case is multiple samples]
    df = df.loc[:, ~df.columns.duplicated(keep="first")]

    # drop records without diagnosis or origin tissue
    df = df[
        (~df["primary_diagnosis"].isna()) & (~df["tissue_or_organ_of_origin"].isna())
    ]

    # add SampleCharacteristic field
    df["SampleCharacteristic"] = (
        df["sample_type"]
        + "_"
        + df["tissue_or_organ_of_origin"]
        + "_"
        + df["primary_diagnosis"]
    )

    df.to_csv(output)


@task(retries=3)
def build_manifest(
    sample_sheet: str = sample_sheet_file,
    min_samples: int = min_samples_per_sample_group,
    base_path: str = manifest_base_path,
) -> None:
    """
    Function to build manifest for each specific group_of_samples present in SampleCharacteristic field.
    Only sample groups containing > min_samples_per_sample_group are processed to further steps.
    Manifest files are exported to location: <base_path / sample group / fileType [Met / Exp] / manifest.txt>.
    Manifest file is an input for GDC download tool.
    """

    logger = get_run_logger()
    sample_sheet = pd.read_csv(sample_sheet)[
        ["id", "experimental_strategy", "SampleCharacteristic"]
    ]
    endpoint = "https://api.gdc.cancer.gov/manifest/"

    for group_of_samples in sample_sheet.SampleCharacteristic.unique():

        # get cases in specific group_of_samples
        partial_sample_sheet = sample_sheet[
            sample_sheet["SampleCharacteristic"] == group_of_samples
        ]

        # get RNA seq files ids
        expression_files = partial_sample_sheet[
            partial_sample_sheet["experimental_strategy"] == "RNA-Seq"
        ]
        expression_files = expression_files["id"].tolist()

        # get methylation files ids
        methylation_files = partial_sample_sheet[
            partial_sample_sheet["experimental_strategy"] == "Methylation Array"
        ]
        methylation_files = methylation_files["id"].tolist()

        # prepare data to request
        to_request = zip(["Exp", "Met"], [expression_files, methylation_files])

        for fileType, files in to_request:
            if len(files) > min_samples:
                # make dir for specific sample group
                makedirs(join(base_path, group_of_samples, fileType), exist_ok=True)

                # build manifest file
                params = {"ids": files}
                resp = requests.post(
                    endpoint,
                    data=json.dumps(params),
                    headers={"Content-Type": "application/json"},
                )
                resp = resp.text

                with open(
                    join(base_path, group_of_samples, fileType, "manifest.txt"), "w"
                ) as file:
                    file.write(resp)

                logger.info(
                    f"Exporting manifest for: {group_of_samples}:{fileType} n samples: {len(files)}"
                )


@task()
def download_methylation_files(base_path: str = manifest_base_path) -> None:
    """
    Function to download methylation files specified in manifest file.
    """
    logger = get_run_logger()
    manifests_met = glob(join(base_path, "*", "Met/manifest.txt"))

    for manifest in manifests_met:
        logger.info(f"Downloading: {manifest}")
        out_dir = str(Path(manifest).parent)

        command = f"{gdc_transfer_tool_executable} download -n {n_process} -m '{manifest}' -d '{out_dir}/'"
        call(command, shell=True)


@task()
def download_expression_files(base_path: str = manifest_base_path) -> None:
    """
    Function to download expression files specified in manifest file.
    """
    logger = get_run_logger()
    manifests_exp = glob(join(base_path, "*", "Exp/manifest.txt"))

    for manifest in manifests_exp:
        logger.info(f"Downloading: {manifest}")
        out_dir = str(Path(manifest).parent)

        command = f"{gdc_transfer_tool_executable} download -n {n_process} -m '{manifest}' -d '{out_dir}/'"
        call(command, shell=True)


@task
def build_frames(
    ftype: str,
    sample_sheet: str = sample_sheet_file,
    base_path: str = manifest_base_path,
    out_dir: str = processed_dir,
) -> None:
    """
    Function to concatenate methylation files into dataframe.
    Final dataframe is exported as parquet file to: <out_dir / sample_group / [ftype].parquet>.
    ftype: str = Met|Exp
    """
    logger = get_run_logger()

    sample_groups = glob(join(base_path, "*/"))
    sample_groups = [str(Path(name).name) for name in sample_groups]
    sample_sheet = pd.read_csv(sample_sheet, index_col=0)

    for sample_group in sample_groups:
        frame = []

        if ftype == "Met":
            files_in = glob(
                join(base_path, sample_group, ftype, "*/", "*level3betas.txt")
            )
        else:
            files_in = glob(
                join(base_path, sample_group, ftype, "*/", "*_star_gene_counts.tsv")
            )

        if files_in:
            for file in files_in:
                file_id = str(Path(file).parent.name)

                sample_id = sample_sheet[sample_sheet["id"] == file_id].index[0]

                if ftype == "Met":
                    sample = pd.read_table(file, header=None, index_col=0)

                else:
                    sample = pd.read_table(file, comment="#")[
                        ["gene_name", "tpm_unstranded"]
                    ]
                    sample = sample.set_index("gene_name")
                    sample = sample[~sample.index.isna()]

                sample.columns = [sample_id]
                sample.index.name = ""
                frame.append(sample)

            makedirs(join(out_dir, sample_group), exist_ok=True)
            frame = pd.concat(frame, axis=1)
            frame = frame.loc[:, ~frame.columns.duplicated(keep="first")]

            frame.to_parquet(
                join(out_dir, sample_group, f"{ftype}.parquet"), index=True
            )
            logger.info(f"Exporting {ftype} frame for {sample_group}: {frame.shape}")


@task
def metadata(final_dir: str = processed_dir) -> None:
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
    final_dir: str = processed_dir,
    min_samples: int = min_common_samples,
    metadata_global_path: str = metadata_global_file,
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

    logger.info(f"Exporting global metadata for whole repository")


@task
def create_repo_summary(
    output_file: str = summary_metafile,
    sample_sheet_path: str = sample_sheet_file,
    metadata_path: str = metadata_global_file,
):
    logger = get_run_logger()
    sample_sheet = pd.read_csv(sample_sheet_path, index_col=0)
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

    logger.info(f"Exporting summary meta file for local repository")


@flow(name="Building data repository")
def run():
    build_directory_tree()
    request_GDC()

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
