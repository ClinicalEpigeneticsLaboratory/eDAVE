n_process = 10
files_limit = 2500
min_common_samples = 10
min_samples_per_sample_group = 5

directory_tree = ("data/raw/", "data/meta/", "data/processed/", "data/interim/")
gdc_raw_response_file = "data/raw/gdc_raw_response.tsv"
sample_sheet_file = "data/meta/sample_sheet.csv"
manifest_base_path = "data/interim"
processed_dir = "data/processed"
metadata_global_file = "data/processed/metadataGlobal"
summary_metafile = "data/processed/summaryMetaFile"

gdc_transfer_tool_executable = (
    "/home/janbinkowski/Desktop/Soft/gdc-client_v1.6.1_Ubuntu_x64/gdc-client"
)

fields_config = [
    "access",
    "data_category",
    "data_format",
    "data_type",
    "experimental_strategy",
    "platform",
    "cases.case_id",
    "cases.samples.sample_type",
    "cases.samples.tissue_type",
    "cases.diagnoses.tissue_or_organ_of_origin",
    "cases.diagnoses.primary_diagnosis",
]

filters_config = {
    "op": "and",
    "content": [
        {
            "op": "in",
            "content": {
                "field": "data_type",
                "value": ["Methylation Beta Value", "Gene Expression Quantification"],
            },
        },
        {
            "op": "in",
            "content": {
                "field": "experimental_strategy",
                "value": ["RNA-Seq", "Methylation Array"],
            },
        },
        {
            "op": "in",
            "content": {
                "field": "cases.samples.sample_type",
                "value": ["Primary Tumor", "Solid Tissue Normal"],
            },
        },
        {
            "op": "in",
            "content": {"field": "data_format", "value": ["txt", "tsv"]},
        },
        {
            "op": "=",
            "content": {"field": "access", "value": "open"},
        },
    ],
}
