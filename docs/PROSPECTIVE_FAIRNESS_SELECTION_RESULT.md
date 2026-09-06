# Prospective Fairness Selection Result

Status: **EXECUTED / DIAGNOSTIC / PROSPECTIVE**

This note records the result of the frozen development-to-holdout fairness-selection protocol without changing the protocol after execution.

## Provenance

- Workflow: `Prospective fairness dev-holdout`
- Workflow run: `34048685428`
- Head SHA: `5539d1cac5258f4c9a1c299425292c72b6d89469`
- Run conclusion: `success`
- Artifact: `prospective-fairness-dev-holdout`
- Artifact ID: `9993893975`
- Artifact digest: `sha256:cba4216ee3ac89697ce890434dddbceed52f7335c047543d4d39ca44ca30d73d`
- Development rows: `240`
- Selected fairness weight: `null`
- Holdout rows: `0`

The workflow passed static checks, unit tests, the frozen development/holdout script, prospective cardinality verification, and artifact upload.

## Frozen gate outcome

The precommitted rule required every development regime to satisfy mean paired predictive-minus-reactive goodput >= -0.001 Mbps. No candidate fairness weight met that requirement, so the protocol correctly selected no weight and did not evaluate the holdout population.

| fairness weight | deadline 0.05 s | deadline 0.5 s | load 1.1 | SNR +3 dB | eligible |
|---:|---:|---:|---:|---:|:---:|
| 0.00 | +0.1210 | +0.1419 | -0.0409 | +0.0307 | no |
| 0.05 | +0.0884 | +0.1544 | -0.0523 | +0.0377 | no |
| 0.10 | +0.0410 | +0.1453 | -0.0823 | +0.0468 | no |
| 0.15 | -0.0170 | +0.1388 | -0.1576 | +0.0267 | no |
| 0.20 | -0.1068 | +0.1232 | -0.2104 | -0.0249 | no |
| 0.30 | -0.3105 | +0.0330 | -0.3943 | -0.1224 | no |

Values are mean paired goodput differences in Mbps on the development population.

## Interpretation

The candidate family failed prospectively because the high-load development regime (`load_1p1`) was harmful for every tested fairness weight, including zero fairness weight. Increasing fairness pressure also progressively worsened tight-deadline and high-load goodput. This means the previous development observation cannot be reduced to a single poorly chosen fairness coefficient: even the throughput-oriented zero-fairness version did not satisfy the frozen cross-regime gate.

The result strengthens the mechanism-level diagnosis that the present predictive utility/service-order design is not robust across operating regions. Prediction can help under moderate deadlines and favorable SNR while harming under congestion, and the sign cannot be repaired by simply retuning fairness weight within the tested family.

## Holdout integrity

Because no candidate passed the development gate, the precommitted failure rule applied. The artifact contains zero holdout rows. Therefore the disjoint holdout seeds remain uninspected by this selection experiment and were not used for tuning or post-hoc model choice.

## Scientific consequence

Do **not** report a selected fairness weight from this experiment. Do **not** claim prospective holdout superiority. The correct result is a prospective negative result for the tested fairness-weight family.

The next scheduler iteration must be treated as a new hypothesis and must use a new prospective development/holdout protocol with fresh seed partitions. It should target the high-load service-order failure directly rather than reusing the untouched holdout population from this failed candidate family for tuning.

This remains synthetic diagnostic evidence and is not canonical WOMD evidence or final publication inference.
