# Model asset

The serialized CatBoost model is distributed separately as a versioned GitHub
Release asset. It is downloaded automatically, verified against the published
SHA-256 digest, and stored in the user's platform cache.

Manual download:

```text
https://github.com/davidmascolo/ITIH/releases/download/v0.1.0/itih_catboost_v1.cbm
```

Expected SHA-256:

```text
d787a8ec308cace285541fbe76aefc3bbe9d2a545c9d3eabe93c87f4041af257
```

The package also supports a manually supplied copy at:

```text
src/itih/assets/itih_catboost_v1.cbm
```

Only the original model used for the reported analyses should be distributed.
Do not retrain a substitute and publish it under the same version.

The published model must satisfy the following release checks:

1. Confirm that its SHA-256 matches `model_metadata.json`.
2. Confirm its feature names and order match the 29 names in `constants.py`.
3. Confirm its class order and the public class mapping using known reference
   samples.
4. Confirm that the model may legally be redistributed. The MIT license at the
   repository root covers the source code, not third-party data, MFP resources,
   or a model artifact unless the rights holder expressly releases it under
   those terms.
