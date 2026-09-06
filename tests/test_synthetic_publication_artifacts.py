from __future__ import annotations

import json
from pathlib import Path

import pytest

from predictive_pc_fmcw.synthetic.publication_artifacts import (
    FIGURES,
    TABLES,
    build_publication_artifact_manifest,
    write_publication_artifact_manifest,
)


def _write(path: Path, payload: dict[str, object] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload or {"ok": True}), encoding="utf-8")


def test_publication_contract_is_exactly_ten_figures_and_eight_tables() -> None:
    assert len(FIGURES) == 10
    assert len(TABLES) == 8
    assert [item.artifact_id for item in FIGURES] == [
        f"Figure{index}" for index in range(1, 11)
    ]
    assert [item.artifact_id for item in TABLES] == [
        "TableI",
        "TableII",
        "TableIII",
        "TableIV",
        "TableV",
        "TableVI",
        "TableVII",
        "TableVIII",
    ]


def test_missing_frozen_evidence_blocks_publication_outputs(tmp_path: Path) -> None:
    _write(tmp_path / "protocol_config.json")
    report = build_publication_artifact_manifest(tmp_path)

    assert report["status"] == "BLOCKED"
    assert report["artifact_count"] == 18
    assert report["blocked_count"] > 0
    figure1 = next(
        row for row in report["artifacts"] if row["artifact_id"] == "Figure1"
    )
    figure3 = next(
        row for row in report["artifacts"] if row["artifact_id"] == "Figure3"
    )
    assert figure1["status"] == "READY"
    assert figure1["inputs"][0]["sha256"]
    assert figure3["status"] == "BLOCKED"
    assert figure3["missing_inputs"] == ["learned_held_out_test.json"]


def test_manifest_refuses_overwrite(tmp_path: Path) -> None:
    destination = tmp_path / "publication.json"
    write_publication_artifact_manifest(tmp_path, destination)
    with pytest.raises(FileExistsError):
        write_publication_artifact_manifest(tmp_path, destination)
