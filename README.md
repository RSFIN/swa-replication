# Anonymous Replication Package: Semantic Work Allocation (SWA)

This repository is the anonymized replication package for the submission on **Semantic Work Allocation (SWA)** and the **Semantic Compilation Boundary (SCB)** in agentic software systems.

It is designed for **double-anonymous review**. No author names, affiliations, personal local paths, credentials, or account identifiers are intentionally included.

## Reviewer quick path

The paper's reported results can be checked **without making any new model/API calls**.

### 1. Install analysis dependencies

```bash
python -m pip install -r requirements.txt
```

### 2. Run the one-command reproduction

```bash
python scripts/analysis/reproduce_all.py
```

This will:

1. validate the 900 planned-run design;
2. reconstruct Table I accuracy from the canonical run-level file;
3. reconstruct reliability, token usage, and request-latency summaries;
4. compare reconstructed summaries with the paper-frozen metric files;
5. write outputs under `reproduced/`;
6. print a concise PASS/WARN report.

For an even shorter check:

```bash
make verify
make reproduce
```

## What is in the package

- `benchmarks/` — frozen B0/B1/B2 task representations and treatment/oracle audit material.
- `configs/` — historical execution configuration, environment-variable templates, and the authoritative paper-analysis protocol.
- `results/run_level/` — canonical 900-run paper-analysis dataset (one row per planned run).
- `results/paper_metrics/` — paper-frozen Table I and Figure 2 metric files.
- `results/audit/` — scoring audit and rescoring changes.
- `results/source_summaries/` — normalized/evaluated historical source summaries and attempt metadata.
- `scripts/analysis/` — validation, metric reconstruction, anonymity scan, and figure reproduction.
- `scripts/historical_harness/` — sanitized historical execution/evaluation code retained for provenance.
- `figures/` — final paper Figure 2 in vector form.
- `docs/` — reviewer guide, artifact manifest, metric definitions, anonymization notes, and paper-to-artifact map.

## Canonical paper-analysis files

- `results/run_level/SWA_900_paper_analysis_runs.csv`
- `results/paper_metrics/Table1_accuracy.csv`
- `results/paper_metrics/Figure2_metrics.csv`
- `results/audit/FINAL_ANSWER_rescoring_audit.csv`
- `results/audit/Claude_rescoring_changes_35.csv`

## Experimental design represented here

The canonical design contains:

- 2 settings: CRMArena-derived and AppWorld-derived frozen-context tasks;
- 5 model families;
- 10 tasks per setting;
- 3 SCB conditions (B0/B1/B2);
- 3 repetitions per task-condition-model cell;
- 900 planned runs in total.

The paper applies a **uniform 300-s analysis budget** to the recorded traces. Historical provider harnesses were heterogeneous; later recoveries after the 300-s budget are excluded from bounded-runtime paper metrics. The authoritative metric definitions are in `configs/paper_analysis_protocol.json`.

## Important distinction: historical execution vs. paper analysis

The historical runners are retained for provenance and inspection, but they are **not** the authoritative definition of the reported metrics. Some providers/runs used different transport timeout or retry behavior. The paper's common analysis protocol is applied retrospectively to the recorded traces and is captured in the canonical 900-run table.

Do not infer the final paper protocol from `configs/execution_config_historical.json`; use `configs/paper_analysis_protocol.json`.

## What can be reproduced without API credentials

Everything needed to check the paper's reported Table I and Figure 2 summaries is included locally. No provider credentials are required for:

- validating the 900-run design;
- reproducing Table I;
- reconstructing Figure 2 metric summaries;
- inspecting B0/B1/B2 treatment material;
- checking rescoring changes and data provenance.

## Optional re-execution

Historical model-call scripts are included only for provenance. Re-executing model calls requires provider credentials and may not reproduce historical hosted-model behavior exactly because provider-side models and infrastructure can change.

## Known paper-frozen latency detail

Reliability and token-usage summaries reconstruct directly from the canonical run-level table. A few GPT/Claude request-latency cells differ by small sub-second amounts when recalculated from normalized timestamps versus the paper-production aggregation. For transparency, `reproduce_all.py` writes both the reconstructed values and a comparison against `results/paper_metrics/Figure2_metrics.csv`. The paper-frozen figure values remain the authoritative values used in the submitted manuscript.

## Anonymity

See `docs/ANONYMIZATION.md` and run:

```bash
python scripts/analysis/check_anonymity.py
```

Benchmark-internal synthetic names/emails may appear inside benchmark-derived task content; they are part of the task state and are not author identifiers.

## Suggested reviewer reading order

1. `docs/REVIEWER_GUIDE.md`
2. `configs/paper_analysis_protocol.json`
3. `docs/PAPER_TO_ARTIFACT_MAP.md`
4. `results/run_level/SWA_900_paper_analysis_runs.csv`
5. `docs/SCORING_AND_METRICS.md`
6. treatment examples under `benchmarks/`

## Repository status during anonymous review

This package intentionally omits author-identifying metadata such as `CITATION.cff`, personal repository links, and named release credits. Those can be added after the anonymous review period.
