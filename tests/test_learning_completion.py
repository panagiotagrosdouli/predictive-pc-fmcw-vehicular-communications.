import json
import tempfile
import unittest
from pathlib import Path

from predictive_pc_fmcw.data.manifest import sha256_file
from predictive_pc_fmcw.learning.ablation import CANONICAL_SEEDS, OBJECTIVES
from predictive_pc_fmcw.learning.completion import verify_completion_manifest


class LearningCompletionTest(unittest.TestCase):
    def _fixture(self, root: Path) -> tuple[Path, Path, list[Path]]:
        dataset = root / "training.npz"
        dataset.write_bytes(b"frozen-training-corpus")
        checkpoints = []
        for objective in OBJECTIVES:
            for seed in CANONICAL_SEEDS:
                path = root / objective / f"seed_{seed}" / "best_comm_aware_gru.pt"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"checkpoint")
                checkpoints.append(path)
        manifest = root / "completion_manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "complete": True,
                    "completed_runs": 20,
                    "expected_runs": 20,
                    "dataset_sha256": sha256_file(dataset),
                    "link_config_sha256": "a" * 64,
                    "objectives": list(OBJECTIVES),
                    "seeds": list(CANONICAL_SEEDS),
                    "checkpoints": [str(path) for path in checkpoints],
                }
            ),
            encoding="utf-8",
        )
        return dataset, manifest, checkpoints

    def test_canonical_completion_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            dataset, manifest, checkpoints = self._fixture(Path(temporary))
            report = verify_completion_manifest(
                manifest, training_npz=dataset, checkpoints=checkpoints
            )
            self.assertEqual(report["status"], "PASS")

    def test_missing_checkpoint_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            dataset, manifest, checkpoints = self._fixture(Path(temporary))
            checkpoints[-1].unlink()
            report = verify_completion_manifest(
                manifest, training_npz=dataset, checkpoints=checkpoints
            )
            self.assertEqual(report["status"], "FAIL")
            self.assertFalse(report["checks"]["supplied_checkpoints_exist"])

    def test_wrong_dataset_hash_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            dataset, manifest, checkpoints = self._fixture(Path(temporary))
            dataset.write_bytes(b"changed-after-training")
            report = verify_completion_manifest(
                manifest, training_npz=dataset, checkpoints=checkpoints
            )
            self.assertEqual(report["status"], "FAIL")
            self.assertFalse(report["checks"]["training_dataset_hash_matches"])

    def test_duplicate_checkpoint_paths_fail(self):
        with tempfile.TemporaryDirectory() as temporary:
            dataset, manifest, checkpoints = self._fixture(Path(temporary))
            duplicate = checkpoints[:-1] + [checkpoints[0]]
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["checkpoints"] = [str(path) for path in duplicate]
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            report = verify_completion_manifest(
                manifest, training_npz=dataset, checkpoints=duplicate
            )
            self.assertEqual(report["status"], "FAIL")
            self.assertFalse(report["checks"]["declared_checkpoint_paths_unique"])
            self.assertFalse(report["checks"]["supplied_checkpoint_paths_unique"])

    def test_incomplete_objective_seed_grid_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            dataset, manifest, checkpoints = self._fixture(root)
            replacement = root / "unexpected" / "seed_999" / "best_comm_aware_gru.pt"
            replacement.parent.mkdir(parents=True, exist_ok=True)
            replacement.write_bytes(b"checkpoint")
            malformed = checkpoints[:-1] + [replacement]
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["checkpoints"] = [str(path) for path in malformed]
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            report = verify_completion_manifest(
                manifest, training_npz=dataset, checkpoints=malformed
            )
            self.assertEqual(report["status"], "FAIL")
            self.assertFalse(report["checks"]["declared_run_grid_complete"])
            self.assertFalse(report["checks"]["supplied_run_grid_complete"])


if __name__ == "__main__":
    unittest.main()
