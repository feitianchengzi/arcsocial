# Operating Model

This is an ArcSocial project-level document. User content lives under
`<workspacePath>`, which defaults to `workspace/`.

## Weekly Rhythm

- Capture inputs continuously in `<workspacePath>/inbox/`.
- Review `<workspacePath>/inbox/ideas/` and select candidates for `<workspacePath>/content/drafts/`.
- Prepare platform-specific versions in `<workspacePath>/platforms/`.
- Move finished items to `<workspacePath>/content/ready/`.
- Archive published versions in `<workspacePath>/content/published/`.
- Record results in `<workspacePath>/data/metrics/`.

## Repository Boundary

ArcSocial stores content operations and reusable tooling. The data workspace
stores personal social publishing data. Neither should become a general notes
archive.

Keep durable personal knowledge elsewhere unless it directly supports social publishing.
