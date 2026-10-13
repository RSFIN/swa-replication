# Reviewer Guide

This guide provides three review paths depending on how much time is available.

## Path A — 60-second integrity check

From the repository root:

```bash
python scripts/analysis/validate_package.py
```

Expected output:

```text
OK: 900 unique planned runs; every benchmark/model/SCB cell has 30 runs.
```

Then inspect:

- `results/paper_metrics/Table1_accuracy.csv`
- `results/paper_metrics/Figure2_metrics.csv`

These are the paper-frozen values used to produce the reported Table I and Figure 2.

## Path B — Reproduce the paper statistics locally

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run:

```bash
python scripts/analysis/reproduce_all.py
```

Outputs are written to `reproduced/`:

- `Table1_accuracy_reconstructed.csv`
- `Figure2_metrics_reconstructed.csv`
- `Figure2_metrics_comparison.csv`
- `reproduction_report.txt`

The script checks the reconstructed Table I values against the paper-frozen values. It also checks reliability/token usage and reports the small known sub-second latency differences in a few GPT/Claude cells.

To regenerate Figure 2 from the paper-frozen metrics:

```bash
python scripts/analysis/plot_figure2.py
```

## Path C — Inspect the architectural treatment

The core treatment is the placement of the Semantic Compilation Boundary (SCB):

- **B0 Runtime-heavy** — primitive state; ER/RR/RF/EC largely deferred to model runtime.
- **B1 Task-localized** — ER/RR/RF shifted into infrastructure; evidence construction remains at runtime.
- **B2 Decision-sufficient** — EC additionally shifted left; aggregation, policy application, and final decision remain runtime responsibilities.

For CRMArena-derived tasks, compare files under:

`benchmarks/crmarena/prompts/`

For AppWorld-derived tasks, compare:

- `benchmarks/appworld/prompts/`
- `benchmarks/appworld/contexts/`

Relevant audits include:

- `benchmarks/crmarena/audit/sufficiency_audit.csv`
- `benchmarks/crmarena/audit/treatment_boundary_audit.csv`
- `benchmarks/appworld/audit.csv`

The sealed oracle files are included so reviewers can inspect how final-answer scoring and treatment-boundary checks were defined.

## Scoring audit

The final paper analysis uses rescored final answers. The package includes:

- `results/audit/FINAL_ANSWER_rescoring_audit.csv`
- `results/audit/Claude_rescoring_changes_35.csv`

The latter contains the 35 Claude labels changed during the scoring audit.

## Historical execution provenance

Historical runner/evaluator code is available under:

`scripts/historical_harness/`

Historical configuration is under:

`configs/model_presets_historical.json`
`configs/execution_config_historical.json`

These files explain how calls were originally executed, but the paper's reported bounded-runtime metrics are defined by:

`configs/paper_analysis_protocol.json`

This distinction is important because historical transport timeouts and retry/recovery behavior were not perfectly uniform across providers.

## No API calls are required for paper verification

The reported summary results can be checked entirely from the included frozen contexts, run-level results, and audit files. Re-executing hosted model calls is optional and not required to validate the paper's reported statistics.
