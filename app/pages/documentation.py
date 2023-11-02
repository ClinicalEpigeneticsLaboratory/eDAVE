import dash
import dash_bootstrap_components as dbc
from dash import dcc

dash.register_page(__name__)

layout = dbc.Container(
    [
        dcc.Markdown(
            """
    ---

    ### Documentation

    ---

    #### Sample(s) type(s)

    We grouped samples deposited in the Genomic Data Commons (GDC) into homogeneous groups,
    named `categories` or `types`, using following strategy:

        sample category = <GDC sample_type> + _ + <GDC tissue or organ of origin> + _ + <GDC primary diagnosis>

    For example: `Primary Tumor_Kidney_Papillary adenocarcinoma, NOS`

    ---

    #### Exclusion/inclusion criteria

    eDAVE is fully based on the GDC repository, but not all of samples
    deposited in the GDC are available via our tool, and it is because:

    1. large files transfer via GDC-API is slow, therefore we created fast accessible local data
    repository. This local database is periodically updated but sometimes may be behind origin GDC database;

    2. if number of samples in specific `category` is > 50, we use 50 randomly selected samples
    with assumption that this sample size is large enough to be representative;

    3. if the number of samples in a particular `category` is < 5, we assume that this sample size is not large enough
    to be representative, so this `category` is not available in our database.

    ---

    #### Scales & units

    Expression levels are expressed as transcripts per million `TPM`:

        TPM ∈ <0, +inf).

    Methylation levels are expressed as beta-values `β-value`:

        β-value ∈ <0, 1>.

    ---

    #### CpG identifiers

    All CpGs targeted by 450K (n≈450.000) and EPIC (n≈850.000) microarrays have a unique identifier (e.g., cg22930808).
    Manifests containing descriptions of targeted CpGs are available from:

    • [EPIC](https://support.illumina.com/downloads/infinium-methylationepic-v1-0-product-files.html)

    • [450K](https://emea.support.illumina.com/downloads/infinium_humanmethylation450_product_files.html)

    **Importantly**, data sets may vary in terms of quality, therefore data sets may differ in number of available to 
    analysis probes (CpGs) .

    ---

    #### Raw data processing pipelines

    Raw data processing pipelines are in details described by the GDC:

    • [EPIC/450K](https://docs.gdc.cancer.gov/Data/Bioinformatics_Pipelines/Methylation_Pipeline/)

    • [RNA-seq](https://docs.gdc.cancer.gov/Data/Bioinformatics_Pipelines/Expression_mRNA_Pipeline/)

    ---

    #### Module 1: Differential features browser

    Differential features browser was designed to identify `differentially expressed genes (DEGs)` or
    `differentially methylated positions (DMPs)` between two categories of samples.

    Process of DMPs/DEGs identification comprises several steps:

    1. extraction of 10% the most variable features (CpGs or genes) in specific dataset;

    2. for each feature, test for normality (Shapiro-Wilk's test)
    and homoscedasticity (Levene's test) at predefined significance level
    (alpha);

    3. Based on results from step 2:
        - if variance between groups is equal and distributions are normal – apply `t-test`;
        - if variance between groups is unequal and distributions are normal – apply `Welch's t-test`;
        - if distributions are not normal – apply `Mann-Whitney-U test`;


    4. Apply Benjamini-Hochberg procedure to control for the false discovery rate;

    5. Calculate `effect size`, expressed as:

        - |delta| = |mean(CpG methylation level in group A) - mean(CpG methylation level in group B)|;
        - FC = mean(gene expression level in group A) / mean(gene expression level in group B)
        - log2(FC) = log2 transformed FC;
        - Hedges` g = standardized mean difference, unlike the metrics described above, Hedges` g is adjusted for
        pooled standard deviation and sample size;

    ---

    #### Module 2: One-dimensional browser

    One-dimensional browser was designed to compare sole variable (CpG
    methylation level or gene expression level) between multiple categories of samples.

    Process of DMP/DEG identification between multiple types of samples comprises several steps:

    1. For selected feature, test for homoscedasticity (Levene's test) and normality (Shapiro-Wilk's test)
    at predefined significance level (alpha);

    2. Based on results from step 1:
        - if variance between groups is equal and distributions are normal - apply `Tukey-HSD post-hoc test`;
        - if variance between groups is unequal and distributions are normal – apply `Games-Howell post-hoc test`;
        - if distributions are not normal - apply `pairwise Man-Whitney-U test with FDR correction`;

    3. Calculate effect size expressed as: delta, fold-change and Hedges` g metrics.

    ---

    #### Module 3: Multi-dimensional browser

    Multi-dimensional browser was designed to identify clusters of
    samples within multidimensional data sets using decomposition methods followed by
    unsupervised clustering algorithms.

    Procedure of clusters identification comprises:

    1. Standardization to unit variance and mean zero;

    2. Decomposition using PCA (principal component analysis) or t-SNE (t-distributed
    stochastic neighbor embedding) algorithms;

    3. Searching, for optimal number of clusters ∈ <2, 10> using Ward's algorithm and Calinski-Harabasz metric;

    4. Finally, an optimal number of clusters is defined as a number
    maximizing Calinski-Harabasz metric (the metric is higher when clusters are dense and well separated).

    ---

    #### Module 4: Association browser

    Association browser was designed to analyse association between CpG
    methylation and gene expression levels, using two independent approaches.


    ##### Module 4.1: Regression-based approach

    using linear model:

        expression level ~ Intercept + methylation level

    or non-linear model based on data transformed using n-degree polynomial transformation (n > 1):

        expression level ~ Intercept + methylation level^1 + methylation level^2 + ... + methylation level^n

    Please note that in case of model estimated using polynomial-transformed dataset **R2 coefficient may be strongly
    inflated**, therefore we recommend to interpret adjusted R2 or AIC/BIC metrics.


    ##### Module 4.2: Bin-based approach

    In the first step, distribution of the methylation level of a selected CpG is divided into n ∈ {2,3,4} sorted and 
    equal-size bins. Then expression levels are compared between these bins using the same approach as described 
    previously in the Module 2.

    ---

    """
        ),
    ],
    fluid=True, className="main-container"
)
