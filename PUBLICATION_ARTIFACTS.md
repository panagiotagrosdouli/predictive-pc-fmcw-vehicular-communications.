# Synthetic Publication Artifact Contract

The dataset-free study requires exactly ten publication figures and eight publication tables. Publication graphics and tables must be generated only from saved experiment/configuration artifacts; missing held-out, OOD, scheduling, robustness, operating-region, or statistical evidence must never be replaced by placeholders or manually entered values.

Run:

```bash
make synthetic-scheduling-protocol
make synthetic-publication-manifest
```

The first command materializes the frozen S0–S7 scheduler protocol as `artifacts/synthetic_dataset_v1/scheduling_protocol.json`. The second command writes `publication_artifacts_manifest.json`, recording READY/BLOCKED status plus SHA-256 provenance for every required input of Figures 1–10 and Tables I–VIII.

A partially READY manifest does **not** mean the paper is ready. For example, architecture/configuration artifacts can be ready before learned models are trained, while held-out result figures remain blocked. Publication readiness requires all frozen experiments and all required evidence to exist and validate.
