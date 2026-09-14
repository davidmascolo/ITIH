from __future__ import annotations

import pandas as pd

from itih.constants import FEATURE_NAMES
from itih.preprocessing import discretize_scores, validate_scores


def make_scores(rows: int = 1, value: float = 0.0) -> pd.DataFrame:
    return pd.DataFrame(
        [[value] * len(FEATURE_NAMES) for _ in range(rows)],
        columns=FEATURE_NAMES,
        index=[f"sample-{index + 1}" for index in range(rows)],
    )


def test_feature_schema_is_stable() -> None:
    assert len(FEATURE_NAMES) == 29
    assert len(set(FEATURE_NAMES)) == 29
    assert FEATURE_NAMES[0] == "MHCI"
    assert FEATURE_NAMES[-1] == "EMT_signature"


def test_discretization_matches_right_closed_training_bins() -> None:
    scores = make_scores()
    scores.loc["sample-1", "MHCI"] = -0.750001
    scores.loc["sample-1", "MHCII"] = -0.75
    scores.loc["sample-1", "Coactivation_molecules"] = -0.749999
    scores.loc["sample-1", "Effector_cells"] = 0.75
    scores.loc["sample-1", "T_cell_traffic"] = 0.750001

    binned = discretize_scores(scores)

    assert binned.loc["sample-1", "MHCI"] == "0"
    assert binned.loc["sample-1", "MHCII"] == "0"
    assert binned.loc["sample-1", "Coactivation_molecules"] == "1"
    assert binned.loc["sample-1", "Effector_cells"] == "1"
    assert binned.loc["sample-1", "T_cell_traffic"] == "2"
    assert set(binned.to_numpy().ravel()) <= {"0", "1", "2"}


def test_validation_reorders_features_without_mutating_input() -> None:
    scores = make_scores(rows=2)
    reversed_scores = scores.loc[:, list(reversed(FEATURE_NAMES))]

    validated = validate_scores(reversed_scores)

    assert tuple(validated.columns) == FEATURE_NAMES
    assert tuple(reversed_scores.columns) == tuple(reversed(FEATURE_NAMES))
    assert all(dtype.kind == "f" for dtype in validated.dtypes)
