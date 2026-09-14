"""Public constants defining the ITIH v1 inference contract."""

from __future__ import annotations

from typing import Final

PACKAGE_VERSION: Final = "0.1.0"
MODEL_VERSION: Final = "1.0"
MODEL_FILENAME: Final = "itih_catboost_v1.cbm"
EXPECTED_TREE_COUNT: Final = 610

LOW_THRESHOLD: Final = -0.75
HIGH_THRESHOLD: Final = 0.75

FEATURE_NAMES: Final[tuple[str, ...]] = (
    "MHCI",
    "MHCII",
    "Coactivation_molecules",
    "Effector_cells",
    "T_cell_traffic",
    "NK_cells",
    "T_cells",
    "B_cells",
    "M1_signatures",
    "Th1_signature",
    "Antitumor_cytokines",
    "Checkpoint_inhibition",
    "Treg",
    "T_reg_traffic",
    "Neutrophil_signature",
    "Granulocyte_traffic",
    "MDSC",
    "MDSC_traffic",
    "Macrophages",
    "Macrophage_DC_traffic",
    "Th2_signature",
    "Protumor_cytokines",
    "CAF",
    "Matrix",
    "Matrix_remodeling",
    "Angiogenesis",
    "Endothelium",
    "Proliferation_rate",
    "EMT_signature",
)

CLASS_LABELS: Final[dict[int, str]] = {
    0: "Hom-D",
    1: "Hom-IE",
    2: "Het-D",
    3: "Het-IE",
}

SCORE_COLUMNS: Final[dict[int, str]] = {
    0: "score_Hom_D",
    1: "score_Hom_IE",
    2: "score_Het_D",
    3: "score_Het_IE",
}
