"""ITIH: single-sample inference of intratumoral immune heterogeneity."""

from .constants import (
    CLASS_LABELS,
    FEATURE_NAMES,
    HIGH_THRESHOLD,
    LOW_THRESHOLD,
    PACKAGE_VERSION,
)
from .predictor import (
    ITIHPredictor,
    IncompatibleModelError,
    ModelDownloadError,
    ModelNotAvailableError,
    calculate_sha256,
    download_model,
    verify_model_checksum,
)
from .preprocessing import (
    InputValidationError,
    discretize_scores,
    prepare_catboost_input,
    prepare_scores,
    validate_scores,
)

__version__ = PACKAGE_VERSION

__all__ = [
    "CLASS_LABELS",
    "FEATURE_NAMES",
    "HIGH_THRESHOLD",
    "ITIHPredictor",
    "IncompatibleModelError",
    "InputValidationError",
    "LOW_THRESHOLD",
    "ModelDownloadError",
    "ModelNotAvailableError",
    "calculate_sha256",
    "discretize_scores",
    "download_model",
    "prepare_catboost_input",
    "prepare_scores",
    "validate_scores",
    "verify_model_checksum",
]
