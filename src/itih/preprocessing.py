"""Input loading, validation, and discretization for ITIH inference."""

from __future__ import annotations

from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd

from .constants import FEATURE_NAMES, HIGH_THRESHOLD, LOW_THRESHOLD

PathLike = Union[str, Path]
ScoreInput = Union[pd.DataFrame, PathLike]


class InputValidationError(ValueError):
    """Raised when an input matrix does not satisfy the ITIH contract."""


def _normalise_sample_index(index: pd.Index) -> pd.Index:
    if isinstance(index, pd.MultiIndex):
        raise InputValidationError("Sample identifiers must use a one-dimensional index.")

    values = pd.Series(index.to_numpy(dtype=object), dtype="object")
    if values.isna().any():
        raise InputValidationError("Sample identifiers cannot be missing.")

    labels = values.map(str)
    if labels.str.strip().eq("").any():
        raise InputValidationError("Sample identifiers cannot be empty.")
    if labels.duplicated().any():
        duplicates = sorted(labels[labels.duplicated(keep=False)].unique())
        raise InputValidationError(
            "Sample identifiers must be unique; duplicates: " + ", ".join(duplicates)
        )

    return pd.Index(labels, name="sample_id")


def validate_scores(scores: pd.DataFrame) -> pd.DataFrame:
    """Validate and order a continuous 29-feature MFP score matrix.

    A defensive float copy is returned. Input columns may be in any order, but
    their names must match :data:`itih.constants.FEATURE_NAMES` exactly.
    """

    if not isinstance(scores, pd.DataFrame):
        raise TypeError("scores must be a pandas DataFrame")
    if scores.shape[0] == 0:
        raise InputValidationError("The input contains no samples.")

    duplicate_columns = scores.columns[scores.columns.duplicated()].tolist()
    if duplicate_columns:
        raise InputValidationError(
            "Feature names must be unique; duplicates: "
            + ", ".join(map(str, duplicate_columns))
        )

    expected = set(FEATURE_NAMES)
    observed = set(scores.columns)
    missing = sorted(expected - observed)
    extra = sorted(observed - expected)
    problems: list[str] = []
    if missing:
        problems.append("missing: " + ", ".join(missing))
    if extra:
        problems.append("unexpected: " + ", ".join(map(str, extra)))
    if problems:
        raise InputValidationError("Invalid feature schema (" + "; ".join(problems) + ").")

    ordered = scores.loc[:, FEATURE_NAMES].copy()
    numeric = ordered.apply(pd.to_numeric, errors="coerce")
    invalid = numeric.isna()
    if invalid.to_numpy().any():
        locations = [
            f"{numeric.index[row]!s}/{numeric.columns[column]}"
            for row, column in np.argwhere(invalid.to_numpy())[:5]
        ]
        raise InputValidationError(
            "All feature values must be numeric and non-missing; invalid values at "
            + ", ".join(locations)
            + (" ..." if invalid.to_numpy().sum() > 5 else "")
        )

    finite = np.isfinite(numeric.to_numpy(dtype=float))
    if not finite.all():
        locations = [
            f"{numeric.index[row]!s}/{numeric.columns[column]}"
            for row, column in np.argwhere(~finite)[:5]
        ]
        raise InputValidationError(
            "All feature values must be finite; invalid values at "
            + ", ".join(locations)
            + (" ..." if (~finite).sum() > 5 else "")
        )

    numeric.index = _normalise_sample_index(numeric.index)
    return numeric.astype(float)


def prepare_scores(
    data: ScoreInput,
    *,
    sample_id_column: str = "sample_id",
) -> pd.DataFrame:
    """Load and validate scores from a DataFrame or tab-separated file.

    Files must contain a named sample identifier column. For DataFrames, that
    column is used when present; otherwise the existing index supplies IDs.
    """

    if isinstance(data, (str, Path)):
        path = Path(data)
        if not path.is_file():
            raise FileNotFoundError(f"Input file not found: {path}")
        frame = pd.read_csv(path, sep="\t")
        if sample_id_column not in frame.columns:
            raise InputValidationError(
                f"Input file must contain a '{sample_id_column}' column."
            )
    elif isinstance(data, pd.DataFrame):
        frame = data.copy()
    else:
        raise TypeError("data must be a pandas DataFrame or a path to a TSV file")

    if sample_id_column in frame.columns:
        sample_index = pd.Index(frame.pop(sample_id_column), name="sample_id")
        frame.index = sample_index

    return validate_scores(frame)


def discretize_scores(
    scores: pd.DataFrame,
    *,
    low_threshold: float = LOW_THRESHOLD,
    high_threshold: float = HIGH_THRESHOLD,
) -> pd.DataFrame:
    """Convert continuous scores to CatBoost categorical strings.

    Bins reproduce ``pandas.cut(..., right=True)`` from the training notebook:
    ``(-inf, low] -> "0"``, ``(low, high] -> "1"``, and
    ``(high, inf) -> "2"``.
    """

    if not low_threshold < high_threshold:
        raise ValueError("low_threshold must be smaller than high_threshold")

    continuous = validate_scores(scores)
    values = continuous.to_numpy(dtype=float)
    binned = np.where(
        values <= low_threshold,
        "0",
        np.where(values <= high_threshold, "1", "2"),
    )
    return pd.DataFrame(
        binned,
        index=continuous.index.copy(),
        columns=FEATURE_NAMES,
        dtype=object,
    )


def prepare_catboost_input(
    data: ScoreInput,
    *,
    sample_id_column: str = "sample_id",
) -> pd.DataFrame:
    """Load, validate, order, and discretize data for the ITIH model."""

    return discretize_scores(prepare_scores(data, sample_id_column=sample_id_column))
