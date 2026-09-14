# Model asset

The serialized CatBoost model is intentionally **not included** in this
repository snapshot. The expected path is:

```text
src/itih/assets/itih_catboost_v1.cbm
```

Only the original model used for the reported analyses should be distributed.
Do not retrain a substitute and publish it under the same version.

Before a release:

1. Place the original `.cbm` file at the path above.
2. Load it with CatBoost and confirm `tree_count_ == 610`.
3. Confirm its feature names and order match the 29 names in `constants.py`.
4. Confirm its class order and the public class mapping using known reference
   samples.
5. Compute SHA-256 and record it in `model_metadata.json`.
6. Change `artifact.included` to `true` and update
   `artifact.verification_status`.
7. Confirm that the model may legally be redistributed. The MIT license at the
   repository root covers the source code, not third-party data, MFP resources,
   or a model artifact unless the rights holder expressly releases it under
   those terms.

If the file is too large for an ordinary Git object, distribute it through a
versioned GitHub Release or Git LFS while retaining the same package path at
installation time.
