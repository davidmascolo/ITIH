"""Command-line interface for ITIH inference."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .predictor import ITIHPredictor, download_model


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="itih",
        description="Infer ITIH classes from 29 normalized MFP signature scores.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    predict_parser = subparsers.add_parser("predict", help="predict ITIH classes")
    predict_parser.add_argument("--input", required=True, type=Path, help="input TSV")
    predict_parser.add_argument("--output", required=True, type=Path, help="output TSV")
    predict_parser.add_argument(
        "--model",
        type=Path,
        default=None,
        help="optional path to itih_catboost_v1.cbm",
    )
    predict_parser.add_argument(
        "--sample-id-column",
        default="sample_id",
        help="sample identifier column (default: sample_id)",
    )
    predict_parser.add_argument(
        "--no-scores",
        action="store_true",
        help="omit the four uncalibrated model-score columns",
    )
    predict_parser.add_argument(
        "--no-download",
        action="store_true",
        help="do not download the release model when it is absent",
    )

    download_parser = subparsers.add_parser(
        "download-model",
        help="download and verify the versioned model",
    )
    download_parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="optional destination (default: platform cache)",
    )
    download_parser.add_argument(
        "--force",
        action="store_true",
        help="replace an existing cached model",
    )
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "download-model":
            model_path = download_model(args.output, force=args.force)
            print(f"Model is available at {model_path}")
            return 0

        predictor = ITIHPredictor.from_pretrained(
            args.model,
            download_if_missing=not args.no_download,
        )
        predictions = predictor.predict(
            args.input,
            sample_id_column=args.sample_id_column,
            include_scores=not args.no_scores,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        predictions.to_csv(args.output, sep="\t", index=False)
    except (FileNotFoundError, ImportError, RuntimeError, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"Wrote {len(predictions)} predictions to {args.output}")
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":  # pragma: no cover
    main()
