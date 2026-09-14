"""High-level API for applying the frozen ITIH CatBoost model."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .constants import (
    CLASS_LABELS,
    EXPECTED_TREE_COUNT,
    FEATURE_NAMES,
    MODEL_FILENAME,
    SCORE_COLUMNS,
)
from .preprocessing import ScoreInput, discretize_scores, prepare_scores


class ModelNotAvailableError(FileNotFoundError):
    """Raised when the separately distributed model asset is absent."""


class IncompatibleModelError(RuntimeError):
    """Raised when a model does not match the public ITIH v1 contract."""


def _as_class_id(value: Any) -> int:
    try:
        number = float(value)
        class_id = int(number)
    except (TypeError, ValueError) as exc:
        raise IncompatibleModelError(f"Invalid CatBoost class value: {value!r}") from exc
    if number != class_id or class_id not in CLASS_LABELS:
        raise IncompatibleModelError(f"Unexpected CatBoost class value: {value!r}")
    return class_id


@dataclass
class ITIHPredictor:
    """Load and apply an ITIH v1 CatBoost model.

    Use :meth:`from_pretrained` to select the packaged asset or a local model
    path. CatBoost is imported lazily so validation and preprocessing remain
    usable before the model file is released.
    """

    model_path: Path
    _model: Any = field(default=None, init=False, repr=False)

    @classmethod
    def from_pretrained(cls, model_path: str | Path | None = None) -> "ITIHPredictor":
        if model_path is None:
            model_path = Path(__file__).parent / "assets" / MODEL_FILENAME
        return cls(Path(model_path).expanduser())

    def _load_model(self) -> Any:
        if self._model is not None:
            return self._model
        if not self.model_path.is_file():
            raise ModelNotAvailableError(
                f"ITIH model asset not found at '{self.model_path}'. "
                "Place the verified 610-tree model at this path or pass "
                "model_path=... to ITIHPredictor.from_pretrained()."
            )

        try:
            from catboost import CatBoostClassifier
        except ImportError as exc:  # pragma: no cover - depends on installation extras
            raise ImportError(
                "CatBoost is required for inference. Install the project with "
                "its runtime dependencies before loading a model."
            ) from exc

        model = CatBoostClassifier()
        model.load_model(str(self.model_path))

        tree_count = getattr(model, "tree_count_", None)
        if tree_count != EXPECTED_TREE_COUNT:
            raise IncompatibleModelError(
                f"Expected {EXPECTED_TREE_COUNT} trees, found {tree_count!r}."
            )

        model_features = tuple(getattr(model, "feature_names_", ()) or ())
        if model_features and model_features != FEATURE_NAMES:
            raise IncompatibleModelError(
                "The model feature names or order do not match the ITIH v1 schema."
            )

        self._model = model
        return model

    @staticmethod
    def _probability_class_order(model: Any, width: int) -> list[int]:
        model_classes = getattr(model, "classes_", None)
        raw_classes = list(model_classes) if model_classes is not None else []
        if not raw_classes:
            params = model.get_all_params()
            raw_classes = list(params.get("class_names", ()) or ())
        if not raw_classes:
            raw_classes = list(range(width))

        class_ids = [_as_class_id(value) for value in raw_classes]
        if len(class_ids) != width or set(class_ids) != set(CLASS_LABELS):
            raise IncompatibleModelError(
                "The model probability columns do not represent all four ITIH classes."
            )
        return class_ids

    def predict(
        self,
        data: ScoreInput,
        *,
        sample_id_column: str = "sample_id",
        include_scores: bool = True,
    ) -> pd.DataFrame:
        """Predict ITIH classes from continuous, normalized 29-feature scores."""

        continuous = prepare_scores(data, sample_id_column=sample_id_column)
        categorical = discretize_scores(continuous)
        model = self._load_model()

        raw_predictions = np.asarray(model.predict(categorical)).reshape(-1)
        class_ids = [_as_class_id(value) for value in raw_predictions]
        result = pd.DataFrame(
            {
                "sample_id": categorical.index,
                "class_id": class_ids,
                "itih_class": [CLASS_LABELS[class_id] for class_id in class_ids],
            }
        )

        if include_scores:
            probabilities = np.asarray(model.predict_proba(categorical), dtype=float)
            if probabilities.ndim != 2 or probabilities.shape[0] != len(result):
                raise IncompatibleModelError("The model returned an invalid score matrix.")
            class_order = self._probability_class_order(model, probabilities.shape[1])
            positions = {class_id: index for index, class_id in enumerate(class_order)}
            for class_id in CLASS_LABELS:
                result[SCORE_COLUMNS[class_id]] = probabilities[:, positions[class_id]]

        return result
