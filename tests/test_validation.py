from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from itih.constants import CLASS_LABELS, EXPECTED_TREE_COUNT, FEATURE_NAMES
from itih import predictor as predictor_module
from itih.predictor import (
    ITIHPredictor,
    IncompatibleModelError,
    ModelNotAvailableError,
    download_model,
)
from itih.preprocessing import InputValidationError, prepare_scores, validate_scores


def make_scores() -> pd.DataFrame:
    return pd.DataFrame(
        [[0.0] * len(FEATURE_NAMES)],
        columns=FEATURE_NAMES,
        index=["sample-1"],
    )


def test_final_class_mapping_is_frozen() -> None:
    assert CLASS_LABELS == {0: "Hom-D", 1: "Hom-IE", 2: "Het-D", 3: "Het-IE"}


@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf, "not-a-number"])
def test_rejects_invalid_values(value: object) -> None:
    scores = make_scores()
    if isinstance(value, str):
        scores["MHCI"] = scores["MHCI"].astype(object)
    scores.loc["sample-1", "MHCI"] = value
    with pytest.raises(InputValidationError):
        validate_scores(scores)


def test_rejects_missing_and_extra_features() -> None:
    missing = make_scores().drop(columns="MHCI")
    with pytest.raises(InputValidationError, match="missing: MHCI"):
        validate_scores(missing)

    extra = make_scores().assign(unexpected=1.0)
    with pytest.raises(InputValidationError, match="unexpected: unexpected"):
        validate_scores(extra)


def test_rejects_duplicate_sample_identifiers() -> None:
    scores = pd.concat([make_scores(), make_scores()])
    with pytest.raises(InputValidationError, match="must be unique"):
        validate_scores(scores)


def test_reads_sample_id_column_from_tsv(tmp_path: Path) -> None:
    table = make_scores().reset_index(names="sample_id")
    path = tmp_path / "scores.tsv"
    table.to_csv(path, sep="\t", index=False)

    loaded = prepare_scores(path)

    assert loaded.index.tolist() == ["sample-1"]
    assert tuple(loaded.columns) == FEATURE_NAMES


def test_missing_model_fails_before_catboost_is_needed(tmp_path: Path) -> None:
    predictor = ITIHPredictor.from_pretrained(tmp_path / "missing.cbm")
    with pytest.raises(ModelNotAvailableError, match="not found"):
        predictor.predict(make_scores())


def test_model_metadata_matches_public_contract() -> None:
    metadata_path = (
        Path(__file__).parents[1] / "src" / "itih" / "assets" / "model_metadata.json"
    )
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    assert metadata["model"]["iterations"] == EXPECTED_TREE_COUNT
    assert metadata["preprocessing"]["feature_count"] == len(FEATURE_NAMES)
    assert metadata["classes"]["mapping"] == {
        str(key): value for key, value in CLASS_LABELS.items()
    }
    assert metadata["artifact"]["included"] is False
    assert metadata["artifact"]["release_tag"] == "v0.1.0"
    assert metadata["artifact"]["download_url"].endswith(
        "/v0.1.0/itih_catboost_v1.cbm"
    )
    assert metadata["artifact"]["sha256"] == (
        "d787a8ec308cace285541fbe76aefc3bbe9d2a545c9d3eabe93c87f4041af257"
    )


def test_download_model_verifies_and_reuses_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = b"synthetic model bytes"
    expected_sha256 = hashlib.sha256(payload).hexdigest()
    metadata = {
        "artifact": {
            "download_url": "https://example.test/itih_catboost_v1.cbm",
            "sha256": expected_sha256,
        }
    }
    monkeypatch.setattr(predictor_module, "load_model_metadata", lambda: metadata)

    calls = []

    def fake_urlopen(request: object, timeout: int) -> io.BytesIO:
        calls.append((request, timeout))
        return io.BytesIO(payload)

    monkeypatch.setattr(predictor_module, "urlopen", fake_urlopen)
    target = tmp_path / "models" / "itih_catboost_v1.cbm"

    assert download_model(target) == target
    assert target.read_bytes() == payload
    assert len(calls) == 1

    assert download_model(target) == target
    assert len(calls) == 1


def test_download_model_discards_checksum_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    metadata = {
        "artifact": {
            "download_url": "https://example.test/itih_catboost_v1.cbm",
            "sha256": hashlib.sha256(b"expected").hexdigest(),
        }
    }
    monkeypatch.setattr(predictor_module, "load_model_metadata", lambda: metadata)
    monkeypatch.setattr(
        predictor_module,
        "urlopen",
        lambda request, timeout: io.BytesIO(b"different"),
    )
    target = tmp_path / "itih_catboost_v1.cbm"

    with pytest.raises(IncompatibleModelError, match="checksum mismatch"):
        download_model(target)

    assert not target.exists()
    assert list(tmp_path.glob("*.part")) == []


def test_probability_scores_follow_public_mapping_not_model_order() -> None:
    class FakeModel:
        classes_ = np.array([3, 2, 0, 1])

        @staticmethod
        def predict(data: pd.DataFrame) -> np.ndarray:
            return np.array([[1]])

        @staticmethod
        def predict_proba(data: pd.DataFrame) -> np.ndarray:
            # Columns follow classes_: Het-IE, Het-D, Hom-D, Hom-IE.
            return np.array([[0.4, 0.3, 0.2, 0.1]])

    predictor = ITIHPredictor.from_pretrained("unused.cbm")
    predictor._model = FakeModel()

    result = predictor.predict(make_scores())

    assert result.loc[0, "class_id"] == 1
    assert result.loc[0, "itih_class"] == "Hom-IE"
    assert result.loc[0, "score_Hom_D"] == pytest.approx(0.2)
    assert result.loc[0, "score_Hom_IE"] == pytest.approx(0.1)
    assert result.loc[0, "score_Het_D"] == pytest.approx(0.3)
    assert result.loc[0, "score_Het_IE"] == pytest.approx(0.4)
