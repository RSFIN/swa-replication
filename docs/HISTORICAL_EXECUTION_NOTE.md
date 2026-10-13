# Historical Execution Note

The formal study was assembled from several execution batches. The batches differ in client timeout/retry/recovery behavior. This heterogeneity is preserved in `results/source_summaries/` and selected historical harness code.

The paper does **not** claim that every historical client physically terminated at exactly 300 s. Instead, the reported bounded-runtime metrics apply a common 300-s analysis budget to the recorded traces. The canonical file `results/run_level/SWA_900_paper_analysis_runs.csv` captures the post-audit paper interpretation of each planned run.

This distinction is important when reading older configuration files whose timeout values may be larger than 300 s.
