# ArcSocial

ArcSocial is an open-source, agent-assisted social publishing workspace. Users
work directly from the ArcSocial project root, while personal articles, assets,
platform drafts, and metrics live in a Git submodule mounted as the data
workspace.

Chinese README: [README.md](README.md).

## Project Boundary

This repository is the open-source project itself.

- `.agents/skills/` stores the reusable agent skills.
- `arckit/` stores this project's ArcKit governance artifacts and project
  memory. It is part of the open-source project, not user content data.
- `docs/`, `playbooks/`, `skills/`, and `tools/` document and support the
  reusable workflow.
- `templates/workspace/` contains the clean starter template for personal
  content data repositories.
- `workspace/` is the recommended mount point for the personal data repository.
  It is usually a Git submodule and is not part of the ArcSocial open-source
  project itself.

User articles, personal drafts, publishing assets, metrics, and private
platform data should live in any independent Git repository mounted into
ArcSocial as a submodule. That data repository can be created from
`templates/workspace/`, or it can be an existing repository that follows the
ArcSocial read/write contract.

## Structure

```text
.agents/               Reusable agent skills for social publishing workflows.
arckit/                ArcKit project artifacts for this open-source project.
docs/                  User and contributor documentation.
playbooks/             Reusable workflows, prompts, checklists, and experiments.
skills/                Future portable skill/package material.
tools/                 Scripts, apps, and tool configuration.
templates/workspace/   Clean starter content workspace for users.
workspace/             Recommended personal data submodule mount point.
```

## Initialize A Personal Data Workspace

Recommended setup from the ArcSocial project root:

```bash
node tools/scripts/init-workspace.mjs --repo <your-content-repo-url> --path workspace
```

If you do not have a personal data repository yet, create one from
`templates/workspace/`:

```bash
node tools/scripts/init-workspace.mjs --new --path workspace
```

ArcSocial writing, adaptation, preview, and publishing workflows should read
and write data under `workspace/`, not personal content in the open-source
project root.

After initialization, run:

```bash
node tools/scripts/doctor.mjs
```

## Content Flow

In the `workspace/` data repository:

1. Capture raw ideas, references, and materials in `inbox/`.
2. Move promising items into `content/drafts/` using `content/drafts/_template.md`.
3. Adapt drafts for each platform under `platforms/`.
4. Move release-ready content into `content/ready/`.
5. After publishing, archive final copy in `content/published/`.
6. Store platform previews, publishing preparation artifacts, and non-secret result records in `publishing/`.
7. Record performance or observations in `data/metrics/` and `playbooks/experiments/`.

## WeChat Official Account Publishing

Final WeChat Official Account draft creation uses the open-source
[`wenyan-mcp`](https://github.com/caol64/wenyan-mcp) foundation. Follow its
official README for installation, `WECHAT_APP_ID` / `WECHAT_APP_SECRET`
configuration, IP whitelist requirements, local mode, and server mode.

`workspace/` may store article source, preview artifacts, and non-secret
publishing records. Do not commit `WECHAT_APP_ID`, `WECHAT_APP_SECRET`,
`appsecret`, or `access_token`.

## Naming

Use date-first names for content files:

```text
YYYY-MM-DD-topic.md
```

Examples:

```text
2026-05-24-agent-workflow.md
2026-05-24-agent-workflow-x.md
2026-05-24-agent-workflow-wechat.md
```

## Operating Rules

- `inbox/` can be messy; everything else should be intentional.
- `content/drafts/` stores the canonical idea before platform adaptation.
- `platforms/` stores platform-specific copy, structure, and constraints.
- `assets/` stores source materials and reusable media, not final post text.
- `publishing/` stores platform publishing preparation artifacts and non-secret result records.
- `playbooks/` captures repeatable methods; `skills/` captures executable or semi-structured abilities.
- `data/` is for planning and measurement, not raw creative notes.
