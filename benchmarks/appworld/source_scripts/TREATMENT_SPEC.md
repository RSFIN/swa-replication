# Frozen AppWorld Treatment Specification

## Common output contract

All three contexts also carry identical public `task_metadata` (task-relative
current datetime and authenticated supervisor email). Context-only oracles use
this metadata and the rendered task instruction; no runtime/API/hidden source is
provided to them.

All B0/B1/B2 prompts use the same response contract:

```text
EVIDENCE_IDS: <JSON array of stable IDs used for the decision>
COMPUTATION: <brief externally verifiable aggregation/ranking summary; no hidden chain-of-thought>
FINAL_ANSWER: <answer in the native AppWorld answer format>
```

`EVIDENCE_IDS` and `COMPUTATION` exist to support trace-level error annotation. They do not ask for private chain-of-thought.

## Family 23cf851 — Venmo likes

Task: sum likes for transactions satisfying a direction/time constraint.

- B0: all of the user's Venmo transactions under a fixed family-level schema.
- B1: only transactions satisfying task direction/time filters, preserving primitive transaction records.
- B2: evidence items `{transaction_id, like_count}` only; no sum.
- Decision execution: sum `like_count`.

This family is intentionally retained as a lower-EC-burden comparison because B1 and B2 are semantically closer than in the other families.

## Family 383cbac — coworkers/manager dinner payments

Task: infer coworkers/manager using Phone, match relevant coworker→manager Venmo social-feed payments, add user's stated share.

- B0: complete family-level contact envelope + broad Venmo social feed; no manager/coworker/restaurant/day filtering. The feed uses natural plain TSV, retaining every row and all original participant names/emails inline. No participant interning, semantic canonicalization, target-dependent filtering, or custom decompression is performed.
- B1: resolved manager/coworkers plus task-relevant feed records, but records are not grouped by coworker/evidence role.
- B2: explicit evidence items mapping each coworker to the matched transaction plus the user's stated share; no sum.
- Decision execution: sum evidence amounts.

## Family fac291d — unique Spotify songs

Task: count unique songs across song, album and playlist libraries.

- B0: three source membership collections.
- B1: explicit source→song membership edges; duplicates remain across sources.
- B2: canonical unique song evidence IDs; no count.
- Decision execution: count unique evidence IDs.

Cross-source deduplication is treated as entity resolution/evidence construction, not aggregation.

## Family 4ec8de5 — release-year Spotify songs

Task: count unique songs satisfying a release-year predicate across song and album libraries.

- B0: direct-song membership + song release metadata + album membership/release metadata.
- B1: source-specific records satisfying the temporal predicate; duplicates remain across sources.
- B2: canonical unique qualifying song IDs; no count.
- Decision execution: count evidence IDs.

## Family 50e1ac9 — top-N genre songs

Task: return top-N most-played songs of a target genre across song/album/playlist libraries.

- B0: source memberships plus song details under a fixed family-level schema; no target-genre filtering.
- B1: target-genre candidate occurrences with source provenance; duplicate song occurrences remain.
- B2: unique song evidence records `{song_id,title,play_count}` in ID order; **not sorted by play_count** and no top-N selection.
- Decision execution: rank by play count and return top N titles.

## No maturity interpretation

B0/B1/B2 are representative SCB placements, not ordered maturity levels. Formal analysis evaluates the resulting quality profiles rather than assuming monotonic accuracy gains.
