"""High-level API for applying the frozen ITIH CatBoost model."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

from .constants import (
    CLASS_LABELS,
    EXPECTED_TREE_COUNT,
    FEATURE_NAMES,
    MODEL_FILENAME,
    PACKAGE_VERSION,
    SCORE_COLUMNS,
)
from .preprocessing import ScoreInput, discretize_scores, prepare_scores


class ModelNotAvailableError(FileNotFoundError):
    """Raised when the separately distributed model asset is absent."""


class ModelDownloadError(RuntimeError):
    """Raised when the versioned model cannot be downloaded safely."""


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


def load_model_metadata() -> dict[str, Any]:
    """Return the model metadata distributed with the package."""

    metadata_path = Path(__file__).parent / "assets" / "model_metadata.json"
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def model_cache_path() -> Path:
    """Return the platform-appropriate cache path for the model asset."""

    override = os.environ.get("ITIH_CACHE_DIR")
    if override:
        cache_dir = Path(override).expanduser()
    elif sys.platform == "darwin":
        cache_dir = Path.home() / "Library" / "Caches" / "itih"
    elif os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        cache_dir = base / "itih" / "Cache"
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
        cache_dir = base / "itih"
    return cache_dir / MODEL_FILENAME


def calculate_sha256(path: str | Path) -> str:
    """Calculate a file's SHA-256 digest without loading it into memory."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_metadata() -> tuple[str, str]:
    artifact = load_model_metadata().get("artifact", {})
    url = artifact.get("download_url")
    expected_sha256 = artifact.get("sha256")
    if not isinstance(url, str) or not url.startswith("https://"):
        raise ModelDownloadError("Model metadata does not contain a valid HTTPS URL.")
    if not isinstance(expected_sha256, str) or len(expected_sha256) != 64:
        raise ModelDownloadError("Model metadata does not contain a valid SHA-256 digest.")
    return url, expected_sha256.lower()


def verify_model_checksum(path: str | Path) -> None:
    """Raise if a model file differs from the published release artifact."""

    _, expected_sha256 = _artifact_metadata()
    observed_sha256 = calculate_sha256(path)
    if observed_sha256.lower() != expected_sha256:
        raise IncompatibleModelError(
            "Model checksum mismatch: the file is incomplete or is not the "
            "published ITIH model."
        )


def download_model(
    destination: str | Path | None = None,
    *,
    force: bool = False,
) -> Path:
    """Download the versioned model, verify SHA-256, and return its path."""

    url, expected_sha256 = _artifact_metadata()
    target = Path(destination).expanduser() if destination else model_cache_path()
    if target.is_file() and not force:
        verify_model_checksum(target)
        return target

    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{MODEL_FILENAME}.",
            suffix=".part",
            dir=target.parent,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            request = Request(
                url,
                headers={"User-Agent": f"itih-predictor/{PACKAGE_VERSION}"},
            )
            with urlopen(request, timeout=120) as response:
                shutil.copyfileobj(response, temporary)

        observed_sha256 = calculate_sha256(temporary_path)
        if observed_sha256.lower() != expected_sha256:
            raise IncompatibleModelError(
                "Downloaded model checksum mismatch; the temporary file was discarded."
            )
        temporary_path.replace(target)
        return target
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise ModelDownloadError(f"Could not download the ITIH model from {url}: {exc}") from exc
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


@dataclass
class ITIHPredictor:
    """Load and apply an ITIH v1 CatBoost model.

    Use :meth:`from_pretrained` to select a local model or retrieve the
    published release asset. CatBoost is imported lazily.
    """

    model_path: Path | None = None
    download_if_missing: bool = True
    _model: Any = field(default=None, init=False, repr=False)

    @classmethod
    def from_pretrained(
        cls,
        model_path: str | Path | None = None,
        *,
        download_if_missing: bool = True,
    ) -> "ITIHPredictor":
        path = Path(model_path).expanduser() if model_path is not None else None
        return cls(path, download_if_missing=download_if_missing)

    def _resolve_model_path(self) -> Path:
        if self.model_path is not None:
            if not self.model_path.is_file():
                raise ModelNotAvailableError(f"ITIH model not found at '{self.model_path}'.")
            verify_model_checksum(self.model_path)
            return self.model_path

        packaged_path = Path(__file__).parent / "assets" / MODEL_FILENAME
        if packaged_path.is_file():
            verify_model_checksum(packaged_path)
            self.model_path = packaged_path
            return packaged_path

        cached_path = model_cache_path()
        if cached_path.is_file():
            verify_model_checksum(cached_path)
            self.model_path = cached_path
            return cached_path

        if not self.download_if_missing:
            raise ModelNotAvailableError(
                "ITIH model is not installed. Enable automatic download or pass "
                "an explicit model_path."
            )

        self.model_path = download_model(cached_path)
        return self.model_path

    def _load_model(self) -> Any:
        if self._model is not None:
            return self._model
        model_path = self._resolve_model_path()

        try:
            from catboost import CatBoostClassifier
        except ImportError as exc:  # pragma: no cover - depends on installation extras
            raise ImportError(
                "CatBoost is required for inference. Install the project with "
                "its runtime dependencies before loading a model."
            ) from exc

        model = CatBoostClassifier()
        model.load_model(str(model_path))

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
