# ITIH

### Single-sample inference of intratumoral immune heterogeneity from bulk RNA sequencing

[![Python](https://img.shields.io/badge/Python-%E2%89%A53.9-3776AB.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-2E8B57.svg)](LICENSE)
[![Article](https://img.shields.io/badge/Clinical%20Cancer%20Research-10.1158%2F1078--0432.CCR--26--1466-8B1A1A.svg)](https://doi.org/10.1158/1078-0432.CCR-26-1466)

**ITIH** is a research software package for inferring intratumoral immune
heterogeneity from a single tumour sample. It applies the classifier described
by Cipriani, Mascolo, Scalera *et al.* to 29 normalized Molecular Functional
Portrait (MFP) signatures derived from bulk RNA-sequencing data.

The method resolves four tumour immune configurations:

| Label | Interpretation |
|---|---|
| **Hom-D** | Homogeneously immune-depleted |
| **Hom-IE** | Homogeneously immune-enriched |
| **Het-D** | Immune-depleted sampled region from a heterogeneous tumour |
| **Het-IE** | Immune-enriched sampled region from a heterogeneous tumour |

> **Research use only.** ITIH is not a diagnostic device and is not validated
> for clinical decision-making or treatment selection.

## Overview

Intratumoral variation in immune composition can be missed when a tumour is
represented by a single biopsy. ITIH was developed from spatially resolved
immune subtyping in the TRACERx421 multi-region NSCLC cohort and enables the
inference of tumour-level immune configuration from an individual sample.

```text
Bulk RNA-seq
     │
     ▼
29 normalized MFP signatures
     │
     ▼
Low / intermediate / high discretization
     │
     ▼
ITIH classifier
     │
     ├── Hom-D
     ├── Hom-IE
     ├── Het-D
     └── Het-IE
```

The repository provides:

- a validated Python interface and command-line application;
- strict input-schema and missing-value checks;
- deterministic preprocessing consistent with model development;
- machine-readable model metadata;
- documentation and synthetic example data.

## Installation

```bash
git clone https://github.com/davidmascolo/ITIH.git
cd ITIH
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Python 3.9 or later is required.

## Model availability

The trained CatBoost model is distributed separately as the versioned GitHub
Release asset `itih_catboost_v1.cbm`. Keeping the binary outside the source
repository makes the codebase lightweight while preserving a fixed,
traceable inference artifact.

On first use, the Python interface downloads the model to the local user cache
and verifies its SHA-256 checksum against
[`model_metadata.json`](src/itih/assets/model_metadata.json). Subsequent runs
reuse the verified local copy.

The model can also be downloaded in advance:

```bash
itih download-model
```

To use a manually downloaded copy, provide its path explicitly:

```python
from itih import ITIHPredictor

predictor = ITIHPredictor.from_pretrained("/path/to/itih_catboost_v1.cbm")
```

The release asset and its checksum are documented in
[`src/itih/assets/README.md`](src/itih/assets/README.md).

## Input data

ITIH expects one sample per row and exactly 29 normalized/scaled MFP signature
scores. Input files must be tab-separated and contain a unique `sample_id`
column.

```text
sample_id    MHCI    MHCII    ...    EMT_signature
sample_01    0.42    0.81     ...   -0.17
```

The package does **not** transform raw read counts, TPM values or gene-level
expression matrices into MFP signatures. Signature generation and scaling must
be compatible with the workflow used for model development.

The continuous scores are discretized as follows:

| Category | Interval |
|---:|---|
| Low | score ≤ -0.75 |
| Intermediate | -0.75 < score ≤ 0.75 |
| High | score > 0.75 |

Feature names, order and detailed validation rules are provided in
[`docs/input_format.md`](docs/input_format.md). A synthetic input table is
available in [`examples/example_input.tsv`](examples/example_input.tsv).

## Command-line usage

```bash
# Optional: download and verify the model before inference
itih download-model

itih predict \
  --input examples/example_input.tsv \
  --output itih_predictions.tsv
```

To use a model stored outside the package:

```bash
itih predict \
  --input signatures.tsv \
  --output predictions.tsv \
  --model /path/to/itih_catboost_v1.cbm
```

## Python usage

```python
from itih import ITIHPredictor

predictor = ITIHPredictor.from_pretrained()
predictions = predictor.predict("examples/example_input.tsv")

print(predictions)
```

The result contains the sample identifier, numeric class, biological label and
class-specific model scores:

```text
sample_id    class_id    itih_class    score_Hom_D    score_Hom_IE    score_Het_D    score_Het_IE
sample_01    1           Hom-IE        ...            ...             ...            ...
```

Model scores are not calibrated probabilities of clinical response, survival
or treatment benefit.

## Use from R

The same `.cbm` artifact can be applied from RStudio or an R session using the
CatBoost R package. It is not opened as an R data file: it is loaded with
`catboost.load_model()`. Input data must retain the documented 29-feature order
and use the same three-level discretization.

```r
library(catboost)

# `x_binned` is a data.frame of the 29 categorical features.
pool <- catboost.load_pool(x_binned)
model <- catboost.load_model("itih_catboost_v1.cbm")
class_id <- as.integer(catboost.predict(model, pool, prediction_type = "Class"))
```

The complete reference script
[`examples/predict.R`](examples/predict.R) downloads and verifies the release
asset, validates and discretizes a TSV input, and writes the four-class result:

```bash
Rscript examples/predict.R signatures.tsv predictions.tsv
```

The Python package remains the reference implementation for input validation
and model inference.

## Reproducibility

The public inference contract is defined by:

- the 29-feature schema and its canonical order;
- the fixed discretization thresholds;
- categorical encoding as strings;
- class mapping `0 Hom-D`, `1 Hom-IE`, `2 Het-D`, `3 Het-IE`;
- the versioned serialized model and its checksum.

Implementation details and provenance are documented in
[`docs/methodology.md`](docs/methodology.md), while intended uses and
limitations are described in [`docs/model_card.md`](docs/model_card.md).

Run the test suite with:

```bash
python -m pip install -e ".[test]"
pytest
```

## Citation

If you use ITIH, please cite:

> Cipriani L, Mascolo D, Scalera S, *et al.* Intratumoral Immune Heterogeneity
> Drives Divergent Outcomes to PD-(L)1 Blockade in Lung Cancer. *Clinical
> Cancer Research*. 2026.
> [doi:10.1158/1078-0432.CCR-26-1466](https://doi.org/10.1158/1078-0432.CCR-26-1466)

Citation metadata for the software and article are available in
[`CITATION.cff`](CITATION.cff).

## License

Source code and documentation are released under the [MIT License](LICENSE).
This license does not automatically cover the serialized model, patient-level
data, third-party MFP resources or the published article. Redistribution terms
for those materials should be reviewed independently.
