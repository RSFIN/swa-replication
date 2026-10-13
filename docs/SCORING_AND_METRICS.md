# Scoring and Metric Definitions

For each benchmark × model × SCB cell there are 10 tasks × 3 repetitions = 30 planned runs.

- **Accuracy**: correct answers / runs that complete within the 300-s budget.
- **Reliability**: runs that complete normally within 300 s / all planned runs.
- **Operational Success**: runs that both complete within 300 s and are correct / all planned runs. This is a derived joint outcome, not a separate quality attribute.
- **Token Usage**: mean input and output tokens over completed-within-budget requests. Missing usage from non-completed calls is not imputed as zero.
- **Request Latency**: median end-to-end request latency over completed-within-budget requests.

The final-answer audit corrected 35 Claude labels (33 false negatives corrected, 2 false positives removed). See `results/audit/`.
