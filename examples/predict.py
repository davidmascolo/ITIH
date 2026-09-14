"""Run ITIH prediction on a TSV file.

Example:
    python examples/predict.py examples/example_input.tsv predictions.tsv
"""

from __future__ import annotations

import argparse
from pathlib import Path

from itih import ITIHPredictor


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--model", type=Path, default=None)
    args = parser.parse_args()

    predictor = ITIHPredictor.from_pretrained(args.model)
    predictions = predictor.predict(args.input)
    predictions.to_csv(args.output, sep="\t", index=False)
    print(predictions.to_string(index=False))


if __name__ == "__main__":
    main()
