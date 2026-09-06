#!/usr/bin/env python3
"""Build the fail-closed publication artifact readiness manifest."""

from __future__ import annotations

import argparse
import json

from predictive_pc_fmcw.synthetic.publication_artifacts import (
    write_publication_artifact_manifest,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="artifacts/synthetic_dataset_v1")
    parser.add_argument(
        "--output",
        default="artifacts/synthetic_dataset_v1/publication_artifacts_manifest.json",
    )
    args = parser.parse_args()

    report = write_publication_artifact_manifest(args.dataset, args.output)
    print(
        json.dumps(
            {
                "status": report["status"],
                "artifact_count": report["artifact_count"],
                "ready_count": report["ready_count"],
                "blocked_count": report["blocked_count"],
                "output": args.output,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
