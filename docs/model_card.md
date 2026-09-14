# ITIH CatBoost v1 model card

## Model summary

ITIH CatBoost v1 is a four-class classifier intended to infer intratumoral
immune heterogeneity configurations from a single NSCLC bulk RNA-seq-derived
sample represented by 29 normalized/scaled MFP signature scores.

| Field | Value |
|---|---|
| Model family | CatBoost multiclass classifier |
| Model version | 1.0 |
| Package version | 0.1.0 |
| Expected artifact | `itih_catboost_v1.cbm` |
| Input dimensionality | 29 categorical features after binning |
| Output classes | Hom-D, Hom-IE, Het-D, Het-IE |
| Artifact distribution | Separate `v0.1.0` GitHub Release asset |

Machine-readable details are in
[`model_metadata.json`](../src/itih/assets/model_metadata.json).

## Intended use

- Retrospective research on NSCLC cohorts with compatible bulk RNA-seq-derived
  MFP signature scores.
- Reproduction or extension of the associated ITIH study.
- Hypothesis generation concerning tumor immune microenvironment
  configurations.

## Out-of-scope use

- Diagnosis, prognosis, treatment selection, or any other clinical decision.
- Direct use with raw counts, TPM, gene-expression matrices, or unscaled ssGSEA
  results.
- Application to a different 29-feature definition based only on similar names.
- Interpretation of model scores as calibrated probabilities of response or
  survival.
- Silent imputation of missing signatures or substitution of alternate
  features.

## Training and evaluation data

The model was developed from 746 tumor regions representing 246 patients in
the TRACERx421 early-stage NSCLC multi-region cohort. A stratified 80/20 split
was used. The scientific study additionally evaluated inferred ITIH in three
independent cohorts totaling 1,085 patients with advanced NSCLC treated with
PD-(L)1 inhibitors and examined concordance with digital pathology.

The repository does not redistribute patient-level training, holdout, or
external validation data.

## Reported performance

The manuscript reports global holdout accuracy of 0.613. For Hom-IE, reported
precision was 0.658, recall 0.694, and F1-score 0.676. These values reflect the
reported experimental split and should not be assumed to transfer unchanged to
another population, assay, sequencing workflow, or signature-normalization
method.

## Limitations and risks

- The inference depends on exact upstream feature construction and scaling.
- The training sample is limited in disease context and cohort composition.
- Intratumoral heterogeneity is inferred from a single sampled region and is
  not a direct spatial measurement.
- Moderate global accuracy means misclassification is expected.
- Batch effects, tumor purity, RNA quality, platform changes, and population
  shift may affect predictions.
- The model scores have not been calibrated as probabilities of clinical
  outcomes.
- Prospective clinical utility has not been established.

Researchers should report assay and preprocessing details, missing-data
handling before ITIH, cohort inclusion criteria, software/model versions, and
the model SHA-256 in publications.

## Ethical considerations

Predicted classes can become correlated with biological, technical, clinical,
or demographic properties not represented adequately in the development data.
Subgroup performance should be evaluated before drawing comparative
conclusions. Do not expose identifiable sample metadata in public prediction
outputs.

## Artifact verification

The versioned release artifact is checked for:

1. the expected model structure;
2. the exact 29 feature names and order;
3. the expected four classes and model-internal class order;
4. agreement with known reference predictions;
5. the SHA-256 digest recorded in the package metadata;
6. documented redistribution rights.

The Python interface verifies the artifact checksum before loading the model.

## Citation and contact

Use [`CITATION.cff`](../CITATION.cff) and cite the associated article:
[doi:10.1158/1078-0432.CCR-26-1466](https://doi.org/10.1158/1078-0432.CCR-26-1466).
Questions and reproducible issue reports should be filed through the GitHub
repository issue tracker.
