.PHONY: install test lint validate benchmark womd ablation matrix paper-quick \
	paper-full motion manifest paper-ablation staged corrected-quick \
	corrected-full paper-draft reproducibility reproduce split-audit stages stage \
	stage2-diagnostic womd-preflight canonical-preflight canonical-stage1 \
	canonical-full synthetic-dataset synthetic-dataset-validate \
	synthetic-training synthetic-training-validate synthetic-baselines \
	synthetic-link-eval synthetic-ablation-plan synthetic-ablation \
	synthetic-pipeline synthetic-freeze synthetic-heldout synthetic-ood \
	synthetic-select-checkpoints synthetic-scheduling-heldout synthetic-scheduling-ood \
	synthetic-stats-heldout synthetic-stats-ood synthetic-learned-heldout \
	synthetic-learned-ood synthetic-robustness-heldout synthetic-robustness-ood \
	synthetic-operating-heldout synthetic-operating-ood synthetic-scheduling-protocol \
	synthetic-publication-manifest

install:
	python -m pip install -e ".[dev]"

test:
	PYTHONPATH=src python -m unittest discover -s tests -v

lint:
	ruff check src tests scripts stages

validate:
	pcfmcw validate --config configs/default.json --output artifacts/validation.json

synthetic-dataset:
	PYTHONPATH=src python scripts/build_synthetic_dataset_v1.py \
		--output artifacts/synthetic_dataset_v1

synthetic-dataset-validate:
	PYTHONPATH=src python scripts/build_synthetic_dataset_v1.py \
		--output artifacts/synthetic_dataset_v1 --validate-only

synthetic-training:
	PYTHONPATH=src python scripts/export_synthetic_training_v1.py \
		--dataset artifacts/synthetic_dataset_v1 \
		--output artifacts/synthetic_dataset_v1/training_dev.npz

synthetic-training-validate:
	PYTHONPATH=src python scripts/export_synthetic_training_v1.py \
		--dataset artifacts/synthetic_dataset_v1 \
		--output artifacts/synthetic_dataset_v1/training_dev.npz --validate-only

synthetic-baselines:
	PYTHONPATH=src python scripts/evaluate_synthetic_baselines_v1.py \
		--dataset artifacts/synthetic_dataset_v1 --split development \
		--output artifacts/synthetic_dataset_v1/development_baselines.json

synthetic-link-eval:
	PYTHONPATH=src python scripts/evaluate_synthetic_link_v1.py \
		--dataset artifacts/synthetic_dataset_v1 --split development \
		--output artifacts/synthetic_dataset_v1/development_link_metrics.json

synthetic-ablation-plan:
	PYTHONPATH=src python scripts/train_synthetic_ablation_v1.py \
		--dataset artifacts/synthetic_dataset_v1/training_dev.npz --plan-only

synthetic-ablation:
	PYTHONPATH=src python scripts/train_synthetic_ablation_v1.py \
		--dataset artifacts/synthetic_dataset_v1/training_dev.npz \
		--output artifacts/synthetic_dataset_v1/learned_ablation

synthetic-pipeline:
	PYTHONPATH=src python scripts/run_synthetic_pipeline_v1.py \
		--output artifacts/synthetic_dataset_v1

synthetic-freeze:
	PYTHONPATH=src python scripts/freeze_synthetic_publication_v1.py

synthetic-select-checkpoints:
	PYTHONPATH=src python scripts/select_synthetic_scheduler_checkpoints_v1.py

synthetic-heldout:
	PYTHONPATH=src python scripts/export_synthetic_official_v1.py \
		--split held_out_test \
		--output artifacts/synthetic_dataset_v1/held_out_test.npz

synthetic-ood:
	PYTHONPATH=src python scripts/export_synthetic_official_v1.py \
		--split ood_test \
		--output artifacts/synthetic_dataset_v1/ood_test.npz

synthetic-learned-heldout:
	PYTHONPATH=src python scripts/evaluate_synthetic_learned_official_v1.py \
		--official-npz artifacts/synthetic_dataset_v1/held_out_test.npz \
		--output artifacts/synthetic_dataset_v1/learned_held_out_test.json

synthetic-learned-ood:
	PYTHONPATH=src python scripts/evaluate_synthetic_learned_official_v1.py \
		--official-npz artifacts/synthetic_dataset_v1/ood_test.npz \
		--output artifacts/synthetic_dataset_v1/learned_ood_test.json

synthetic-scheduling-heldout:
	PYTHONPATH=src python scripts/run_synthetic_scheduling_v1.py \
		--split held_out_test

synthetic-scheduling-ood:
	PYTHONPATH=src python scripts/run_synthetic_scheduling_v1.py \
		--split ood_test

synthetic-stats-heldout:
	PYTHONPATH=src python scripts/analyze_synthetic_scheduling_v1.py \
		--input artifacts/synthetic_dataset_v1/scheduling_held_out_test.json \
		--output artifacts/synthetic_dataset_v1/statistics_held_out_test.json

synthetic-stats-ood:
	PYTHONPATH=src python scripts/analyze_synthetic_scheduling_v1.py \
		--input artifacts/synthetic_dataset_v1/scheduling_ood_test.json \
		--output artifacts/synthetic_dataset_v1/statistics_ood_test.json

synthetic-robustness-heldout:
	PYTHONPATH=src python scripts/run_synthetic_robustness_v1.py \
		--split held_out_test

synthetic-robustness-ood:
	PYTHONPATH=src python scripts/run_synthetic_robustness_v1.py \
		--split ood_test

synthetic-operating-heldout:
	PYTHONPATH=src python scripts/run_synthetic_operating_region_v1.py \
		--split held_out_test

synthetic-operating-ood:
	PYTHONPATH=src python scripts/run_synthetic_operating_region_v1.py \
		--split ood_test

synthetic-scheduling-protocol:
	PYTHONPATH=src python scripts/materialize_synthetic_scheduling_protocol_v1.py

synthetic-publication-manifest:
	PYTHONPATH=src python scripts/build_synthetic_publication_manifest_v1.py

benchmark:
	pcfmcw benchmark --config configs/default.json --output artifacts/synthetic_benchmark

womd:
	pcfmcw benchmark --config configs/default.json \
		--womd-export data/example/womd_trajectories.json \
		--max-vehicles 5 --output artifacts/womd_proxy_benchmark

ablation:
	pcfmcw ablation --config configs/default.json \
		--output artifacts/horizon_ablation --horizons 3 5 10 20

matrix:
	pcfmcw matrix --config configs/default.json \
		--matrix configs/experiment_matrix.json \
		--output artifacts/experiment_matrix

motion:
	pcfmcw motion-eval --config configs/default.json \
		--output artifacts/motion_baselines

manifest:
	python scripts/00_freeze_paper_manifest.py

split-audit:
	@test -n "$(TRAIN_NPZ)" -a -n "$(VALIDATION_NPZ)" || \
		(echo "Set TRAIN_NPZ and VALIDATION_NPZ"; exit 2)
	PYTHONPATH=src python scripts/00_audit_womd_split_integrity.py \
		training=$(TRAIN_NPZ) official_validation=$(VALIDATION_NPZ)

womd-preflight:
	@test -n "$(WOMD_ROOTS)" || (echo "Set WOMD_ROOTS to files/directories"; exit 2)
	PYTHONPATH=src python scripts/womd_preflight.py $(WOMD_ROOTS) \
		--output womd_preflight.json

canonical-preflight:
	@test -n "$(WOMD_DATA_ROOT)" -a -n "$(TRAIN_NPZ)" -a -n "$(VALIDATION_NPZ)" || \
		(echo "Set WOMD_DATA_ROOT, TRAIN_NPZ and VALIDATION_NPZ"; exit 2)
	PYTHONPATH=src python scripts/00_preflight_canonical_execution.py \
		--data-root "$(WOMD_DATA_ROOT)" --train-npz "$(TRAIN_NPZ)" \
		--validation-npz "$(VALIDATION_NPZ)" $(CANONICAL_PREFLIGHT_ARGS)

canonical-stage1: canonical-preflight
	PYTHONPATH=src python scripts/run_canonical_womd_pipeline.py \
		--data-root "$(WOMD_DATA_ROOT)" --train-npz "$(TRAIN_NPZ)" \
		--validation-npz "$(VALIDATION_NPZ)" --mode stage1

canonical-full:
	@test -n "$(VALIDATION_GLOB)" || (echo "Set VALIDATION_GLOB"; exit 2)
	$(MAKE) canonical-preflight CANONICAL_PREFLIGHT_ARGS='--full --require-gpu \
		--validation-glob "$(VALIDATION_GLOB)" $(EXTRA_PREFLIGHT_ARGS)'
	PYTHONPATH=src python scripts/run_canonical_womd_pipeline.py \
		--data-root "$(WOMD_DATA_ROOT)" --train-npz "$(TRAIN_NPZ)" \
		--validation-npz "$(VALIDATION_NPZ)" \
		--validation-glob "$(VALIDATION_GLOB)" --mode full \
		$(LAMBDA_ARGS)

stages:
	PYTHONPATH=src python scripts/run_research_stage.py

stage:
	@test -n "$(STAGE)" || (echo "Set STAGE=stage0 ... stage8"; exit 2)
	PYTHONPATH=src python scripts/run_research_stage.py --stage $(STAGE) $(EXECUTE)

stage2-diagnostic:
	PYTHONPATH=src python scripts/02_diagnose_part_a_receiver.py

paper-ablation:
	pcfmcw paper-ablation --config configs/default.json \
		--ber-lut artifacts/ber/dbpsk_ber_lut.csv \
		--output artifacts/paper_run/paper_ablations

paper-quick:
	PYTHONPATH=src python scripts/run_paper_pipeline.py --quick \
		--output artifacts/paper_run
	PYTHONPATH=src python scripts/build_paper_pdf.py

paper-full:
	PYTHONPATH=src python scripts/run_paper_pipeline.py \
		--output artifacts/paper_run_full

staged:
	PYTHONPATH=src python scripts/07_run_staged_experiments.py \
		--config configs/default.json \
		--output artifacts/staged_experiments

corrected-quick:
	PYTHONPATH=src python scripts/run_corrected_pipeline.py --quick \
		--output artifacts/corrected_v2_quick

corrected-full:
	PYTHONPATH=src python scripts/run_corrected_pipeline.py \
		--output artifacts/corrected_v2

paper-draft:
	PYTHONPATH=src python scripts/build_paper_pdf.py

reproducibility:
	PYTHONPATH=src python scripts/build_reproducibility_manifest.py \
		--output artifacts/corrected_v2/reproducibility_manifest.json

reproduce: test lint corrected-quick paper-draft reproducibility
