# Input format

ITIH accepts a UTF-8, tab-separated table containing one sample per row. The
file must include a `sample_id` column and exactly 29 continuous feature
columns.

```text
sample_id<TAB>MHCI<TAB>MHCII<TAB>...<TAB>EMT_signature
sample_001<TAB>0.42<TAB>0.81<TAB>...<TAB>-0.17
```

See [`examples/example_input.tsv`](../examples/example_input.tsv) for a complete
synthetic file. Its values demonstrate the format only and do not represent
patients or expected biological profiles.

## Required features

Names are case-sensitive. The canonical order is:

1. `MHCI`
2. `MHCII`
3. `Coactivation_molecules`
4. `Effector_cells`
5. `T_cell_traffic`
6. `NK_cells`
7. `T_cells`
8. `B_cells`
9. `M1_signatures`
10. `Th1_signature`
11. `Antitumor_cytokines`
12. `Checkpoint_inhibition`
13. `Treg`
14. `T_reg_traffic`
15. `Neutrophil_signature`
16. `Granulocyte_traffic`
17. `MDSC`
18. `MDSC_traffic`
19. `Macrophages`
20. `Macrophage_DC_traffic`
21. `Th2_signature`
22. `Protumor_cytokines`
23. `CAF`
24. `Matrix`
25. `Matrix_remodeling`
26. `Angiogenesis`
27. `Endothelium`
28. `Proliferation_rate`
29. `EMT_signature`

Columns may appear in another order; the package validates and restores this
order. Missing, unexpected, or duplicate columns are rejected.

## Value requirements

Every feature value must be numeric and finite. Empty cells, `NaN`, positive or
negative infinity, and text are rejected. The package does not impute missing
values.

Values must be normalized/scaled MFP signature scores generated with a workflow
compatible with model training. ITIH deliberately does not infer or guess the
required transformation from raw counts, TPM, `log2(TPM+1)`, or raw ssGSEA
output.

## Threshold boundaries

The training notebook used `pandas.cut` with its default right-closed
intervals. ITIH preserves those edge semantics exactly:

- `score <= -0.75` becomes categorical string `"0"`;
- `-0.75 < score <= 0.75` becomes categorical string `"1"`;
- `score > 0.75` becomes categorical string `"2"`.

Consequently, `-0.75` belongs to the low bin and `+0.75` belongs to the
intermediate bin.

## Sample identifiers

`sample_id` values must be present and unique after conversion to text. They are
copied unchanged in meaning to the prediction output and are never supplied to
the classifier as a feature.

For an in-memory `pandas.DataFrame`, either provide `sample_id` as a column or
store sample identifiers in the index. A custom file-column name can be passed
with `--sample-id-column` or the corresponding Python argument.

## Output fields

Default output contains:

- `sample_id`: identifier from the input;
- `class_id`: integer `0` through `3`;
- `itih_class`: `Hom-D`, `Hom-IE`, `Het-D`, or `Het-IE`;
- `score_Hom_D`, `score_Hom_IE`, `score_Het_D`, `score_Het_IE`: uncalibrated
  CatBoost multiclass scores on the probability scale.

The score columns are not calibrated probabilities of response, survival, or
clinical benefit.
