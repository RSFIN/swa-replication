# SWA Experimental Data Re-audit — 2026-10-05

## 1. Corpus integrity
- 900 unique planned results were retained: 2 benchmarks × 10 tasks × 3 SCB conditions × 5 models × 3 repetitions.
- Uniqueness key: `(benchmark, model, repeat, task, condition)`; duplicates: 0.
- Every `(benchmark, model, task, condition)` cell contains exactly 3 repetitions.
- These are planned experimental results, not raw HTTP-attempt counts.

## 2. FINAL_ANSWER re-scoring
- CRM GPT/Claude records in the comparison bundle were re-parsed from the declared `FINAL_ANSWER:` field.
- GPT-5.6: 0 correctness-label changes after robust `FINAL_ANSWER` parsing.
- Claude Opus 5.5: 35 correctness-label changes: 33 false negatives corrected and 2 false positives revoked.
- The original Claude scorer sometimes captured an earlier agent ID appearing in evidence/reasoning rather than the declared final answer.

## 3. Corrected headline results
### CRMArena — operational success within the 300-s analysis threshold
- B0: 46/150 = 30.7%
- B1: 114/150 = 76.0%
- B2: 146/150 = 97.3%

### CRMArena — 3/3 repeatability across 50 model–task pairs
- B0: 7/50 = 14%
- B1: 32/50 = 64%
- B2: 47/50 = 94%

### AppWorld
- Operational success: 144/150 = 96%, 147/150 = 98%, 150/150 = 100% for B0/B1/B2.
- 3/3 repeatability: 45/50 = 90%, 48/50 = 96%, 50/50 = 100%.

## 4. Metric definitions to use in the paper
- `final_answer_correct`: correctness of the declared final answer irrespective of the 300-s analysis threshold.
- `operational_success_300`: `final_answer_correct == 1 AND recorded_latency <= 300 s`.
- `repeatability_3of3`: a model–task pair has operational success in all three repetitions.
- `observed input-token burden`: provider-reported input tokens only; no calibration/imputation is applied.
- `recorded request latency`: recorded wall-clock request latency; no post-hoc 300-s capping is applied to the latency statistic.

## 5. Input-token missingness
- 79/900 records lack provider-reported input-token usage.
- Missingness is concentrated in timeout/failure-heavy conditions and is therefore potentially non-random.
- Figure 2 should show only observed token medians and disclose `n` for cells with fewer than 30 observed values; Qwen–CRMArena–B0 is NA (n=0).

## 6. Important interpretation corrections
- DeepSeek CRMArena B0 has 30/30 correct final answers, but only 18/30 finish within the 300-s analysis threshold. The 60% value is therefore an operational-success/timeliness metric, not pure accuracy.
- The previous claim that Claude CRMArena B2 achieved only 60% was an evaluator artifact; after re-scoring it is 30/30 final-answer correct and 30/30 operationally successful within 300 s.
- The corrected data support strong B0→B2 operational improvement, but no longer support a strong systematic “failure migration” mechanism claim.
