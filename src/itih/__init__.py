"""ITIH: single-sample inference of intratumoral immune heterogeneity."""

from .constants import (
    CLASS_LABELS,
    FEATURE_NAMES,
    HIGH_THRESHOLD,
    LOW_THRESHOLD,
    PACKAGE_VERSION,
)
from .predictor import ITIHPredictor, IncompatibleModelError, ModelNotAvailableError
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
    "ModelNotAvailableError",
    "discretize_scores",
    "prepare_catboost_input",
    "prepare_scores",
    "validate_scores",
]
