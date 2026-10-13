# Artifact Manifest

## Top level

- `README.md`: reviewer-facing landing page and quick-start instructions.
- `REVIEWER_GUIDE.md` is located under `docs/`.
- `Makefile`: convenience targets for validation/reproduction.
- `requirements.txt`: analysis dependencies.
- `ARTIFACT_VERSION`: anonymous artifact version identifier.
- `SHA256SUMS.txt`: integrity hashes for package contents.

## `benchmarks/`

- `crmarena/prompts/`: frozen B0/B1/B2 inputs for the 10 selected CRMArena-derived tasks.
- `crmarena/audit/`: context-length, sufficiency, and treatment-boundary audits.
- `crmarena/sealed/`: oracle material used by the evaluator.
- `appworld/prompts/` and `appworld/contexts/`: frozen B0/B1/B2 inputs for the AppWorld-derived tasks.
- `appworld/sealed/`: oracle/audit material.
- `appworld/source_scripts/`: compiler/audit scripts used to construct the AppWorld formal bundle.

## `configs/`

- `model_presets_historical.json`: historical model endpoints/model IDs and reasoning settings; secrets are environment-variable names only.
- `execution_config_historical.json`: historical harness configuration; retained for provenance, not as the paper metric definition.
- `paper_analysis_protocol.json`: authoritative definitions for the reported 300-s analysis and paper metrics.
- `env.example`: empty credential template.
- `requirements_analysis.txt`: analysis dependencies.
- `requirements_historical_harness.txt`: minimal historical-runner dependency list.

## `scripts/analysis/`

- `validate_package.py`: validates 900 unique planned runs and the 30-run benchmark/model/SCB cells.
- `reproduce_table1.py`: reconstructs Table I conditional accuracy.
- `reproduce_runtime_metrics.py`: reconstructs runtime metric summaries.
- `reproduce_all.py`: reviewer-oriented one-command reproduction and comparison report.
- `plot_figure2.py`: regenerates Figure 2 from the paper-frozen metric file.
- `check_anonymity.py`: scans repository metadata/code/config/results for common anonymity/credential leaks.

## `scripts/historical_harness/`

Selected original runner/evaluator modules with personal paths and credentials removed. These are retained for provenance and should not be confused with the final paper-analysis protocol.

## `results/`

- `run_level/`: canonical 900-run paper-analysis dataset.
- `paper_metrics/`: paper-frozen summary values for Table I and Figure 2.
- `audit/`: rescoring and data-audit material.
- `source_summaries/`: evaluated/attempt summaries from heterogeneous historical runs; raw hidden-reasoning payloads are intentionally omitted.

## `figures/`

- `Figure2.pdf` / `Figure2.svg`: final paper figure.

## `docs/`

- `REVIEWER_GUIDE.md`: 60-second, local-reproduction, and treatment-inspection paths.
- `PAPER_TO_ARTIFACT_MAP.md`: maps claims/tables/figures to source files and scripts.
- `EXPECTED_RESULTS.md`: numerical checkpoints.
- `REPRODUCIBILITY.md`: reproduction details.
- `SCORING_AND_METRICS.md`: metric definitions.
- `HISTORICAL_EXECUTION_NOTE.md`: distinction between historical execution and paper analysis.
- `ANONYMIZATION.md`: anonymization policy.
- `REPOSITORY_SETUP.md`: anonymous-repository upload checklist.
- `UPSTREAM_DATA_NOTICE.md`: upstream/redistribution considerations.

## `reproduced/`

Generated locally by the analysis scripts. The directory is ignored by Git except for `.gitkeep`.
