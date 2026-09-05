#!/usr/bin/env python3
"""Compute scenario-level paired statistics for synthetic scheduling results."""

from __future__ import annotations

import argparse
import json

from predictive_pc_fmcw.synthetic.scheduling_statistics import analyze_scheduling_file


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--bootstrap-samples", type=int, default=5000)
    args = parser.parse_args()
    report = analyze_scheduling_file(
        args.input,
        args.output,
        bootstrap_samples=args.bootstrap_samples,
    )
    print(
        json.dumps(
            {
                "status": "COMPLETED",
                "inferential_unit": report["inferential_unit"],
                "output": args.output,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
