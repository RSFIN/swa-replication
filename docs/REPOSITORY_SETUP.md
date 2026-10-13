# Anonymous Repository Setup Checklist

This package is already arranged to be uploaded to an anonymous review repository.

## Before upload

1. Use a fresh anonymous repository/service account not linked to an author identity.
2. Do not reuse a personal Git commit history.
3. Upload the **contents** of this package as a fresh repository snapshot.
4. Keep `CITATION.cff`, author lists, affiliations, acknowledgements, and personal project URLs out of the anonymous repository.
5. Do not upload `.env`, API keys, billing/account exports, or private provider dashboards.
6. Run:

```bash
python scripts/analysis/check_anonymity.py
python scripts/analysis/validate_package.py
```

7. Confirm `README.md` renders correctly on the hosting service.
8. Confirm the anonymous URL works in a private/incognito browser session without login.
9. Replace `ANONYMOUS-URL` in the manuscript Data Availability statement only after the anonymous repository is live.

## Recommended repository landing page

Use the included top-level `README.md` unchanged or with only hosting-specific navigation edits. It deliberately starts with the no-API reviewer path.

## Do not expose during double-anonymous review

- author names or initials tied to affiliations;
- university/lab/company names that identify the authors;
- personal GitHub usernames;
- local filesystem usernames or home directories;
- API keys, organization IDs, billing IDs, or private endpoint aliases;
- issue/commit history from a non-anonymous repository;
- acknowledgements or grant identifiers that directly identify the group.

## After acceptance

The anonymous snapshot can be migrated to a public repository and an archival DOI service. At that stage, add author metadata, citation metadata, license information as appropriate, and a versioned release corresponding to the camera-ready paper.
