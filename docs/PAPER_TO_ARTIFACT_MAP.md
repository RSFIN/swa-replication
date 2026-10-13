# Paper-to-Artifact Map

This file maps the main empirical claims and paper elements to artifact files.

| Paper element / claim | Artifact source | Reproduction / audit |
|---|---|---|
| Experimental design: 900 planned runs | `results/run_level/SWA_900_paper_analysis_runs.csv` | `scripts/analysis/validate_package.py` |
| SCB definition and B0/B1/B2 treatment | `benchmarks/**`, `configs/paper_analysis_protocol.json` | `docs/REVIEWER_GUIDE.md` |
| Table I: conditional accuracy | `results/run_level/SWA_900_paper_analysis_runs.csv` | `scripts/analysis/reproduce_table1.py` |
| Table I paper-frozen values | `results/paper_metrics/Table1_accuracy.csv` | compared by `reproduce_all.py` |
| Figure 2(a): reliability | canonical 900-run file | `reproduce_runtime_metrics.py` / `reproduce_all.py` |
| Figure 2(b): token usage | canonical 900-run file | `reproduce_runtime_metrics.py` / `reproduce_all.py` |
| Figure 2(c): request latency | canonical 900-run file + paper-frozen aggregation | `reproduce_all.py` comparison report |
| Figure 2 paper-frozen values | `results/paper_metrics/Figure2_metrics.csv` | `scripts/analysis/plot_figure2.py` |
| Final Figure 2 | `figures/Figure2.pdf`, `figures/Figure2.svg` | regenerated into `reproduced/` |
| 300-s analysis budget | `configs/paper_analysis_protocol.json` | canonical `completed_within_300s` field |
| Operational success | canonical `operational_success_300` field | recomputed in `reproduce_all.py` |
| Final-answer scoring audit | `results/audit/FINAL_ANSWER_rescoring_audit.csv` | audit inspection |
| 35 changed Claude labels | `results/audit/Claude_rescoring_changes_35.csv` | audit inspection |
| Historical execution provenance | `scripts/historical_harness/`, `results/source_summaries/` | `docs/HISTORICAL_EXECUTION_NOTE.md` |
| Anonymous-review safeguards | `docs/ANONYMIZATION.md` | `scripts/analysis/check_anonymity.py` |
