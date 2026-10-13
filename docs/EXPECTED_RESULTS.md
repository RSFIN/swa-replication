# Expected Results

The following values provide quick checkpoints for a successful reproduction.

## Table I — pooled conditional accuracy (%)

| Setting | B0 | B1 | B2 |
|---|---:|---:|---:|
| CRMArena | 52.9 | 94.2 | 98.0 |
| AppWorld | 98.0 | 98.0 | 100.0 |

Selected model-level checks:

- CRMArena / DeepSeek / B0: 100.0% conditional accuracy among 18 completed requests.
- CRMArena / Qwen / B0: N/A because no request completed within the 300-s budget.
- CRMArena / Claude / B0: 13.3% conditional accuracy.

## Reliability checkpoints (%)

- CRMArena / DeepSeek / B0: 60.0
- CRMArena / Doubao / B0: 43.3
- CRMArena / Qwen / B0: 0.0
- CRMArena / GPT / B0: 80.0
- CRMArena / Claude / B0: 100.0
- AppWorld / Qwen / B0: 90.0

## Operational-success pooled checkpoints (%)

- CRMArena: B0 = 30.0, B1 = 76.0, B2 = 97.3
- AppWorld: B0 = 96.0, B1 = 98.0, B2 = 100.0

## Figure 2

The authoritative paper-frozen values are in:

`results/paper_metrics/Figure2_metrics.csv`

The plotting script uses this file directly. Small sub-second latency differences may appear when reconstructing medians from normalized run-level timestamps; these are reported rather than silently overwritten.
