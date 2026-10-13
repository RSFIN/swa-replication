# Anonymization Notes

The package was prepared for double-anonymous review.

Removed or excluded:
- author names and affiliations;
- personal/local absolute paths and local usernames;
- API keys and credentials;
- machine-specific worker logs containing local environment paths;
- raw provider response payloads containing hidden/reasoning content;
- Git metadata / author metadata.

Retained intentionally:
- model/provider names needed to interpret the experiment;
- public API base URLs where present in historical configuration;
- benchmark task identifiers;
- synthetic names/emails embedded in AppWorld-derived benchmark state (these are benchmark content, not author identifiers);
- timestamps and request metadata when required to reconstruct runtime-budget behavior.

Before public release after acceptance, replace the anonymous package URL with a stable public repository/archive and re-check upstream benchmark redistribution terms.
