# Methodology

## Scientific objective

Intratumoral immune heterogeneity (ITIH) describes the coexistence of
immune-enriched and immune-depleted regions within a tumor. The associated
study developed a classifier that infers a tumor-level immune configuration
from a single bulk RNA-seq-derived sample.

The model was developed using 746 tumor regions from 246 patients in the
TRACERx421 multi-region NSCLC cohort. Region-level immune states and 29
microenvironment-related signatures were derived through the Molecular
Functional Portrait (MFP) framework. The dataset was split into stratified 80%
training and 20% holdout subsets with random seed 123.

## Supported inference pipeline

This package implements only the stable final inference stages:

1. validate a matrix of 29 normalized/scaled MFP signature scores;
2. restore the exact training feature order;
3. discretize each continuous score into low, intermediate, or high;
4. represent every category as a string for CatBoost;
5. apply the frozen multiclass CatBoost model;
6. map numeric predictions to the four public ITIH labels.

The upstream RNA-seq-to-signature workflow is not implemented. The manuscript
describes `log2(TPM+1)` expression, ssGSEA through GSVA in R, and subsequent
discretization. However, safe transfer of the classifier requires that users
reproduce the same normalization/scaling used to create the model inputs, not
merely the same gene-set scoring algorithm. This separation also avoids
redistributing third-party MFP code or resources under incompatible terms.

## Discretization

For a continuous signature score `x`, the encoded categorical value is:

```text
0  if x <= -0.75
1  if -0.75 < x <= 0.75
2  if x > 0.75
```

The resulting values are passed to CatBoost as strings (`"0"`, `"1"`, `"2"`),
matching the inference cells in the source notebook.

## Frozen model configuration

The v1 model contract records:

| Parameter | Value |
|---|---:|
| Algorithm | `CatBoostClassifier` |
| Loss | `MultiClass` |
| Iterations / trees | 610 |
| Depth | 9 |
| Learning rate | 0.05 |
| L2 leaf regularization | 8 |
| Bagging temperature | 1 |
| Random strength | 0.5 |
| Random seed | 123 |
| Training CatBoost version | 1.2.10 |

Class weighting was used during training and is recorded in
`model_metadata.json`. GPU was selected for training, but inference with the
serialized model is supported on CPU.

## Class semantics

The public mapping is fixed as:

```text
0 -> Hom-D
1 -> Hom-IE
2 -> Het-D
3 -> Het-IE
```

`Hom-D` and `Hom-IE` denote homogeneous immune-depleted and immune-enriched
tumors, respectively. `Het-D` denotes an immune-depleted sampled region from a
tumor inferred to contain both immune states; `Het-IE` is the analogous class
for an immune-enriched sampled region.

The serialized CatBoost model records its own probability-column class order.
The predictor reads that order and then reports scores in the stable public
order above.

## Reported evaluation

The associated manuscript reports a holdout accuracy of 0.613. For the Hom-IE
class, which the optimization prioritized for recall, reported precision was
0.658, recall 0.694, and F1-score 0.676. These are study estimates, not package
acceptance-test results; independent reproduction requires the original model,
holdout data, and frozen environment.

## Reference

Laura Cipriani, Davide Mascolo, Stefano Scalera, et al. *Intratumoral Immune
Heterogeneity Drives Divergent Outcomes to PD-(L)1 Blockade in Lung Cancer.*
Clinical Cancer Research. 2026.
[doi:10.1158/1078-0432.CCR-26-1466](https://doi.org/10.1158/1078-0432.CCR-26-1466).
