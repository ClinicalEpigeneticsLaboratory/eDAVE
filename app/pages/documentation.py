import dash
import dash_bootstrap_components as dbc
from dash import dcc

dash.register_page(__name__)

layout = dbc.Container(
    dcc.Markdown(
        """
    ---

    ### Documentation

    ---

    #### Sample(s) type(s)

    We grouped samples deposited in Genomic Data Commons (GDC) into homogenous groups,
    named `types`, using following strategy:

        sample type = <GDC sample_type> + _ + <GDC tissue or organ of origin> + _ + <GDC primary diagnosis>

    ---

    #### Exclusion/inclusion criteria

    eDAVE is fully based on GDC repository, but not all of cases
    deposited in GDC are available via our tool, and it is because:

    1. large files transfer via GDC-API is slow, thus we created, fast accessible local data
    repository. This local database is periodically updated but sometimes may be outdated in
    comparison to origin GDC database;

    2. if number of samples in specific type is > 50, we used 50 randomly selected instances
    with assumption that this sample size is large enough to be representative;

    3. if number of samples in specific type is < 10, we assumed that this sample size is not
    large enough to be representative, thus excluded from our local data repository.

    ---

    #### Scales

    Expression levels are expressed as transcripts per million `TPM`.

        TPM ∈ <0, +inf)

    Methylation levels are expressed as beta-values `β-value`.

        β-value ∈ <0, 1>.

    ---

    #### Raw data processing


    Raw data processing pipelines are in details described by GDC:

    • [EPIC/450K](https://docs.gdc.cancer.gov/Data/Bioinformatics_Pipelines/Methylation_Pipeline/)

    • [RNA-seq](https://docs.gdc.cancer.gov/Data/Bioinformatics_Pipelines/Expression_mRNA_Pipeline/)

    ---

    #### Module 1: Differential features browser

    Differential features browser was designed to identify `differentially expressed genes
    (DEGs)` or `differentially methylated positions (DMPs)` between types of samples.

    Process of DMPs/DEGs identification is comprising several steps:

    1. Extraction of 10% most variable features (CpGs or genes) in specific dataset
     based on standard deviation.

    2. For each feature, test for normality (Shapiro-Wilk test)
    and homoscedasticity (Levene`s test) at predefined significance level
    (alpha).

    3. Based on results from step 2:
        - if variance between groups are equal and distributions are normal – apply t-test
        - if variance between groups are unequal and distributions are normal – apply Welch's t-test
        - if distributions are not normal – apply Mann-Whitney-U test


    4. Apply Benjamini-Hochberg procedure to control the false discovery rate.

    5. Calculate effect size:

        - For CpG methylation expressed as:

                |delta| = |mean(CpG methylation level in group A) - mean(CpG methylation level in group B)|

        - For gene expression expressed as:

                FC = log2(mean(gene expression level in group A) / mean(gene expression level in group B))

    ---

    #### Module 2: One-dimensional browser

    One-dimensional browser was designed to compare sole variable (CpG
    methylation level or gene expression level) across multiple
    samples types.

    Process of DMP/DEG identification between multiple samples types is comprising several steps:

    1. For selected feature, test for homoscedasticity (Levene`s test) at predefined significance level (alpha).

    2. Based on results from step 1:
        - if variances between groups are equal apply `Tukey-HSD post-hoc test`
        - if variances between groups are unequal – apply `Games-Howell post-hoc test`


    3. Calculate effect size expressed as: delta, fold-change, Cohen's d metric.

    ---

    #### Module 3: Multi-dimensional browser

    Multi-dimensional browser was designed to identify clusters of
    samples within multidimensional datasets using unsupervised clustering and
    decomposition algorithms.

    Procedure:

    1. Scale dataset (nxm) congaing n-number of samples and m-number of
    features (genes or CpGs).

    2. Apply PCA (principal component analysis) or t-SNE (t-distributed
    stochastic neighbor embedding) decomposition algorithm on scaled
    dataset.

    3. Iteratively, for each predefined number of clusters ∈ <2, 10> apply
    Ward algorithm and calculate Calinski-Harabasz index.

    4. Finally an optimal number of clusters is defined as a number
    maximizing Calinski-Harabasz metric.

    ---

    #### Module 4: Association browser

    Association browser was designed to analyse association between CpG
    methylation and gene expression.

    To assess association between quantitative variables, we propose linear model :

        expression level ~ Intercept + methylation level

    or non-linear model (using polynomial transformation, degree > 1):

        expression level ~ Intercept + methylation level^1 + methylation level^2 + methylation level^n

    In these models, estimated coefficients express strength of association
    between expression and methylation levels. Additionally to asses significance of estimated effect
    Wald`s test is performed.

    Models goodness-of fit is expressed in form of multiple different
    coefficients, such as: R2, adjusted R2, Log-Likelihood, Akaike
    information content (AIC) and Bayesian information content (BIC).

    The higher values of `R2`, `adjusted R2` and `Log-Likelihood` indicates
    a better fit of the model. While lower `AIC` and `BIC` indicate less complex
    and/or better fit models.

    Please note in case of non-linear models **R2 coefficient may be strongly
    inflated**, so adjusted R2 or AIC/BIC metrics should be interpreted.

    """
    )
)
