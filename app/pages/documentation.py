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

    We grouped samples deposited in Genomic Data Commons (GDC) into homogeneous groups,
    named `types`, using following strategy:

        sample type = <GDC sample_type> + _ + <GDC tissue or organ of origin> + _ + <GDC primary diagnosis>

    For example: `Primary Tumor_Kidney_Papillary adenocarcinoma, NOS`

    ---

    #### Exclusion/inclusion criteria

    eDAVE is fully based on GDC repository, but not all of samples
    deposited in GDC are available via our tool, and it is because:

    1. large files transfer via GDC-API is slow, thus we created fast accessible local data
    repository. This local database is periodically updated but sometimes may be outdated in
    comparison to origin GDC database;

    2. if number of samples in specific type is > 50, we used 50 randomly selected instances
    with assumption that this sample size is large enough to be representative;

    3. if the number of samples in a particular type is < 10, we assumed that this sample size
    is not large enough to be representative, so it was excluded from our local data repository;

    ---

    #### Scales & units

    Expression levels are expressed as transcripts per million `TPM`:

        TPM ∈ <0, +inf).

    Methylation levels are expressed as beta-values `β-value`:

        β-value ∈ <0, 1>.

    ---

    #### CpG identifiers

    All CpGs targeted by 450K (n≈450.000) and EPIC (n≈850.000) microarrays have a unique identifier, for example cg22930808.
    Manifests containing all of targeted CpGs along with genomic context for specific technology are available from:

    • [EPIC](https://support.illumina.com/downloads/infinium-methylationepic-v1-0-product-files.html)

    • [450K](https://emea.support.illumina.com/downloads/infinium_humanmethylation450_product_files.html)

    Importantly, not all of the 450,000 CpG targeted by the 450K microarray are present in the EPIC.
    In addition, some probes may not pass quality control and will not be available for analysis in specific dataset.

    ---

    #### Raw data processing pipelines

    Raw data processing pipelines are in details described by GDC:

    • [EPIC/450K](https://docs.gdc.cancer.gov/Data/Bioinformatics_Pipelines/Methylation_Pipeline/)

    • [RNA-seq](https://docs.gdc.cancer.gov/Data/Bioinformatics_Pipelines/Expression_mRNA_Pipeline/)

    ---

    #### Module 1: Differential features browser

    Differential features browser was designed to identify `differentially expressed genes (DEGs)` or
    `differentially methylated positions (DMPs)` between different types of samples.

    Process of DMPs/DEGs identification comprises several steps:

    1. extraction of 10% most variable features (CpGs or genes) in specific dataset
    based on standard deviation;

    2. for each feature, test for normality (Shapiro-Wilk's test)
    and homoscedasticity (Levene's test) at predefined significance level
    (alpha);

    3. Based on results from step 2:
        - if variance between groups are equal and distributions are normal – apply `t-test`;
        - if variance between groups are unequal and distributions are normal – apply `Welch's t-test`;
        - if distributions are not normal – apply `Mann-Whitney-U test`;


    4. Apply Benjamini-Hochberg procedure to control the false discovery rate;

    5. Calculate `effect size`, expressed as:

        - |delta| = |mean(CpG methylation level in group A) - mean(CpG methylation level in group B)|;
        - FC = mean(gene expression level in group A) / mean(gene expression level in group B)
        - log2(FC) = log2(FC);
        - Hedges` g = standardized mean difference, in contrary to above described metrics, this one takes in to account
        the pooled standard deviation and the size of both groups of samples;

    ---

    #### Module 2: One-dimensional browser

    One-dimensional browser was designed to compare sole variable (CpG
    methylation level or gene expression level) between multiple
    samples types.

    Process of DMP/DEG identification between multiple samples types comprises several steps:

    1. For selected feature, test for homoscedasticity (Levene's test) and normality (Shapiro-Wilk's test)
    at predefined significance level (alpha);

    2. Based on results from step 1:
        - if variance between groups are equal and distributions are normal - apply `Tukey-HSD post-hoc test`;
        - if variance between groups are unequal and distributions are normal – apply `Games-Howell post-hoc test`;
        - if distributions are not normal - apply `pairwise Man-Whitney-U test with FDR correction`;


    3. Calculate effect size expressed as: delta, fold-change and Hedges` g metrics;

    ---

    #### Module 3: Multi-dimensional browser

    Multi-dimensional browser was designed to identify clusters of
    samples within multidimensional datasets using unsupervised clustering and
    decomposition algorithms.

    Procedure of clusters identification comprises:

    1. Re-scale to unit variance and mean zero dataset (nxm) congaing n-number
    of samples and m-number of features (genes or CpGs);

    2. Apply PCA (principal component analysis) or t-SNE (t-distributed
    stochastic neighbor embedding) decomposition algorithm on scaled
    dataset;

    3. Iteratively, for each predefined number of clusters ∈ <2, 10> apply
    Ward's algorithm and calculate Calinski-Harabasz metric (variance ratio criterion);

    4. Finally, an optimal number of clusters is defined as a number
    maximizing Calinski-Harabasz metric (the metric is higher when clusters are dense and well separated);

    ---

    #### Module 4: Association browser

    Association browser was designed to analyse association between CpG
    methylation and gene expression.

    To assess association between quantitative variables, we propose linear model:

        expression level ~ Intercept + methylation level

    or non-linear model based on data transformed using n-degree polynomial transformation (n > 1):

        expression level ~ Intercept + methylation level^1 + methylation level^2 + methylation level^n

    In these models, estimated coefficient(s) express(es) strength of CpG methylation influence on gene expression level.
    To asses significance of estimated effect Wald`s test is performed.

    Model performance is expressed in form of multiple different
    parameters, such as: R2, adjusted R2, Log-Likelihood, Akaike
    information content (AIC) and Bayesian information content (BIC).
    Larger values of `R2`, `adjusted R2` and `Log Likelihood` indicate a better fit of the model to the data.
    Lower `AIC` and `BIC` indicate less complex and/or better fit model.

    Please note in case of model estimated using polynomial-transformed dataset **R2 coefficient may be strongly
    inflated**, therefore adjusted R2 or AIC/BIC metrics should be interpreted.

    """
        ),
        dbc.Row(style={"height": "15vh"}),
    ],
    fluid=True,
)
