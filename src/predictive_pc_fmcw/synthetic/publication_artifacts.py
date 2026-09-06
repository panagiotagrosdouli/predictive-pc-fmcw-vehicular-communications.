"""Fail-closed publication artifact provenance for the synthetic study."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from ..data.manifest import sha256_file


@dataclass(frozen=True)
class PublicationArtifactSpec:
    artifact_id: str
    title: str
    kind: str
    required_inputs: tuple[str, ...]


FIGURES = (
    PublicationArtifactSpec(
        "Figure1",
        "System architecture and causal information flow",
        "figure",
        ("protocol_config.json",),
    ),
    PublicationArtifactSpec(
        "Figure2",
        "Example synthetic trajectories and noisy observations",
        "figure",
        ("manifest.json", "protocol_config.json"),
    ),
    PublicationArtifactSpec(
        "Figure3",
        "Held-out ADE and FDE comparison",
        "figure",
        ("learned_held_out_test.json",),
    ),
    PublicationArtifactSpec(
        "Figure4",
        "Held-out communication prediction errors",
        "figure",
        ("learned_held_out_test.json",),
    ),
    PublicationArtifactSpec(
        "Figure5",
        "Held-out scheduler comparison",
        "figure",
        ("scheduling_held_out_test.json", "statistics_held_out_test.json"),
    ),
    PublicationArtifactSpec(
        "Figure6",
        "Deadline-miss rate versus mobility difficulty",
        "figure",
        ("operating_region_held_out_test/analysis.json",),
    ),
    PublicationArtifactSpec(
        "Figure7",
        "Goodput versus prediction horizon",
        "figure",
        ("operating_region_held_out_test/analysis.json",),
    ),
    PublicationArtifactSpec(
        "Figure8",
        "Predictive-gain operating-region heatmap",
        "figure",
        ("operating_region_held_out_test/analysis.json",),
    ),
    PublicationArtifactSpec(
        "Figure9",
        "Communication-aware objective ablation",
        "figure",
        ("learned_held_out_test.json",),
    ),
    PublicationArtifactSpec(
        "Figure10",
        "Robustness under observation and channel uncertainty",
        "figure",
        ("robustness_held_out_test/manifest.json", "learned_ood_test.json"),
    ),
)

TABLES = (
    PublicationArtifactSpec(
        "TableI",
        "Simulation and PC-FMCW/DPSK link parameters",
        "table",
        ("protocol_config.json",),
    ),
    PublicationArtifactSpec(
        "TableII",
        "Synthetic mobility parameter ranges and split policy",
        "table",
        ("protocol_config.json", "manifest.json"),
    ),
    PublicationArtifactSpec(
        "TableIII",
        "Predictor and scheduler definitions",
        "table",
        ("development_baselines.json", "scheduling_protocol.json"),
    ),
    PublicationArtifactSpec(
        "TableIV",
        "Held-out trajectory prediction results",
        "table",
        ("learned_held_out_test.json",),
    ),
    PublicationArtifactSpec(
        "TableV",
        "Held-out communication prediction results",
        "table",
        ("learned_held_out_test.json",),
    ),
    PublicationArtifactSpec(
        "TableVI",
        "End-to-end scheduling results",
        "table",
        ("scheduling_held_out_test.json",),
    ),
    PublicationArtifactSpec(
        "TableVII",
        "Training-objective ablation",
        "table",
        ("learned_held_out_test.json",),
    ),
    PublicationArtifactSpec(
        "TableVIII",
        "Paired statistical tests and effect sizes",
        "table",
        ("statistics_held_out_test.json",),
    ),
)


def _inspect_input(root: Path, relative_path: str) -> dict[str, object]:
    path = root / relative_path
    if not path.is_file():
        return {
            "path": relative_path,
            "present": False,
            "sha256": None,
        }
    return {
        "path": relative_path,
        "present": True,
        "sha256": sha256_file(path),
    }


def build_publication_artifact_manifest(
    dataset_dir: str | Path,
) -> dict[str, object]:
    """Build readiness state without inventing missing publication evidence."""
    root = Path(dataset_dir)
    records: list[dict[str, object]] = []
    for spec in (*FIGURES, *TABLES):
        inputs = [_inspect_input(root, item) for item in spec.required_inputs]
        ready = all(bool(item["present"]) for item in inputs)
        records.append(
            {
                **asdict(spec),
                "status": "READY" if ready else "BLOCKED",
                "inputs": inputs,
                "missing_inputs": [
                    str(item["path"]) for item in inputs if not item["present"]
                ],
            }
        )

    ready_count = sum(row["status"] == "READY" for row in records)
    return {
        "protocol": "synthetic_dataset_v1_publication_artifacts",
        "status": "READY" if ready_count == len(records) else "BLOCKED",
        "artifact_count": len(records),
        "ready_count": ready_count,
        "blocked_count": len(records) - ready_count,
        "figures_expected": 10,
        "tables_expected": 8,
        "artifacts": records,
        "scientific_guards": {
            "saved_artifacts_only": True,
            "no_placeholder_metrics": True,
            "no_manual_publication_values": True,
            "missing_frozen_evidence_blocks_output": True,
        },
    }


def write_publication_artifact_manifest(
    dataset_dir: str | Path,
    output_path: str | Path,
) -> dict[str, object]:
    report = build_publication_artifact_manifest(dataset_dir)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(
            f"refusing to overwrite publication artifact manifest: {destination}"
        )
    destination.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report
