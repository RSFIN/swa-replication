# Reproducibility Guide

## A. Reproduce the reported statistics without new API calls

From the repository root:

```bash
python -m pip install -r requirements.txt
python scripts/analysis/reproduce_all.py
```

The script validates the 900-run design, reconstructs Table I, reconstructs Figure 2 metrics, compares them to the paper-frozen summaries, and writes outputs under `reproduced/`.

Expected high-level status:

- Table I: exact reconstruction.
- Figure 2 reliability / completed-count / input-output token summaries: exact reconstruction from the canonical run-level table.
- Request latency: small sub-second differences may occur in a few GPT/Claude cells because normalized run-level timestamps and the paper-production aggregation were generated from slightly different timestamp representations. The script reports the maximum difference rather than hiding it.

## B. Regenerate Figure 2

```bash
python scripts/analysis/plot_figure2.py
```

This uses the paper-frozen metrics in `results/paper_metrics/Figure2_metrics.csv` and writes:

- `reproduced/Figure2_reproduced.pdf`
- `reproduced/Figure2_reproduced.svg`
- `reproduced/Figure2_reproduced_600dpi.png`

## C. Inspect the treatment

For any task, compare its B0/B1/B2 representation under `benchmarks/`.

- B0: runtime-heavy / primitive state.
- B1: task-localized; ER/RR/RF shifted to infrastructure.
- B2: decision-sufficient; EC additionally shifted left, while aggregation/policy/final decision remain at runtime.

Relevant sufficiency and treatment-boundary audits are included under each benchmark directory.

## D. Inspect the scoring audit

See:

- `results/audit/FINAL_ANSWER_rescoring_audit.csv`
- `results/audit/Claude_rescoring_changes_35.csv`

The latter contains the 35 changed Claude labels found in the final-answer audit.

## E. Historical model-call re-execution

The historical harness is preserved under `scripts/historical_harness/`, but it is provenance rather than the authoritative paper protocol. Re-execution requires provider credentials supplied through the environment-variable names listed in `configs/env.example`.

A clean future rerun should use a hard 300-s wall-clock watchdog, fixed retry semantics, balanced condition order, and pinned model/configuration manifests.
