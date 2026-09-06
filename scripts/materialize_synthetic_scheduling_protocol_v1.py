#!/usr/bin/env python3
"""Materialize the frozen S0-S7 scheduler protocol as a saved artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from predictive_pc_fmcw.synthetic.scheduling_protocol import (
    scheduler_protocol_manifest,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="artifacts/synthetic_dataset_v1/scheduling_protocol.json",
    )
    args = parser.parse_args()

    destination = Path(args.output)
    if destination.exists():
        raise FileExistsError(
            f"refusing to overwrite scheduling protocol artifact: {destination}"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    report = scheduler_protocol_manifest()
    destination.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": "COMPLETED", "output": args.output}, indent=2))


if __name__ == "__main__":
    main()
