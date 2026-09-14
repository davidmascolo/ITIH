# ITIH

**Single-sample inference of intratumoral immune heterogeneity from 29
normalized Molecular Functional Portrait (MFP) signatures.**

ITIH packages the inference step described in:

> Cipriani L, Mascolo D, Scalera S, et al. *Intratumoral Immune Heterogeneity
> Drives Divergent Outcomes to PD-(L)1 Blockade in Lung Cancer.* Clinical
> Cancer Research. 2026. https://doi.org/10.1158/1078-0432.CCR-26-1466

The classifier assigns a single bulk RNA-seq-derived sample to one of four
microenvironmental configurations:

| Class ID | Label | Interpretation |
|---:|---|---|
| 0 | Hom-D | Homogeneously immune-depleted |
| 1 | Hom-IE | Homogeneously immune-enriched |
| 2 | Het-D | Immune-depleted sampled region from a heterogeneous tumor |
| 3 | Het-IE | Immune-enriched sampled region from a heterogeneous tumor |

> [!IMPORTANT]
> The original serialized model is not included in this repository snapshot.
> Preprocessing and validation are fully usable and tested, but prediction
> requires the verified 610-tree model at
> `src/itih/assets/itih_catboost_v1.cbm`.

## Scientific scope

The supported workflow starts with **29 normalized/scaled MFP signature
scores**, not a raw gene-expression matrix:

```text
bulk RNA-seq
    |
    v
29 normalized MFP signatures (upstream; not implemented here)
    |
    v
low / intermediate / high using -0.75 and +0.75
    |
    v
ITIH CatBoost v1 (610 trees)
    |
    v
Hom-D / Hom-IE / Het-D / Het-IE
```

Users must generate the signature scores with a pipeline compatible with the
one used for model development. Raw ssGSEA values, TPM values, counts, or an
independently scaled matrix must not be passed directly to the classifier.
See [input format](docs/input_format.md) and
[methodology](docs/methodology.md).

## Installation

```bash
git clone https://github.com/davidmascolo/ITIH.git
cd ITIH
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Copy the verified model to:

```text
src/itih/assets/itih_catboost_v1.cbm
```

The model must contain 610 trees and use the exact feature schema documented
in this repository. Release checks are listed in
[`src/itih/assets/README.md`](src/itih/assets/README.md).

## Quick start

Command line:

```bash
itih predict \
  --input examples/example_input.tsv \
  --output itih_predictions.tsv
```

Use a model stored elsewhere with `--model /path/to/model.cbm`.

Python:

```python
from itih import ITIHPredictor

predictor = ITIHPredictor.from_pretrained()
predictions = predictor.predict("examples/example_input.tsv")
print(predictions)
```

The output contains `sample_id`, `class_id`, `itih_class`, and four CatBoost
score columns. These scores are model outputs and are **not calibrated clinical
probabilities**. Pass `include_scores=False` in Python or `--no-scores` on the
command line to omit them.

## Input contract

- One sample per row.
- A unique, non-empty `sample_id` column.
- Exactly the 29 case-sensitive feature names in the documented schema.
- Numeric, finite, non-missing continuous scores.
- Any column order is accepted; the package reorders features to the frozen
  training order before inference.

The discretization reproduces the right-closed intervals used in the training
notebook:

| Encoded value | Continuous interval |
|---:|---|
| `"0"` | score <= -0.75 |
| `"1"` | -0.75 < score <= 0.75 |
| `"2"` | score > 0.75 |

## Reproducibility contract

The public v1 contract is frozen in code, metadata, and tests:

- 29 ordered features;
- thresholds `-0.75` and `+0.75`;
- categorical values supplied to CatBoost as strings;
- class mapping `0 Hom-D`, `1 Hom-IE`, `2 Het-D`, `3 Het-IE`;
- expected CatBoost tree count: 610;
- training configuration and provenance in
  [`model_metadata.json`](src/itih/assets/model_metadata.json).

The predictor also uses the class ordering stored in the CatBoost artifact when
aligning score columns. This is necessary because model-internal class order
need not be numeric order.

## Testing without the model

```bash
python -m pip install -e ".[test]"
pytest
```

The current tests exercise schema validation, boundary behavior, class mapping,
metadata consistency, and the expected missing-model error. Prediction
regression tests should be added when the original `.cbm` and reference samples
are available.

## Intended use and limitations

ITIH is research software for applying the published classifier to compatible
NSCLC bulk RNA-seq-derived signature data. It is not a diagnostic device, is
not validated for treatment selection, and should not be used for clinical
decision-making. Generalization beyond the studied setting or after changing
the upstream signature pipeline has not been established. See the full
[model card](docs/model_card.md).

## Citation

Please cite both the software (using [`CITATION.cff`](CITATION.cff)) and the
associated article above. GitHub will expose the software citation after this
repository is published.

## License

The Python source code and documentation are released under the
[MIT License](LICENSE). This license does not automatically apply to the
CatBoost model artifact, study data, third-party MFP resources, or the journal
article. Verify redistribution rights before adding any of those materials.
