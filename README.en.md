# ArcSocial

ArcSocial is an open-source, agent-assisted social content workspace. It is not
a Web/App service and does not need a long-running server. Users work directly
from the ArcSocial project root with an agent to plan topics, write drafts,
adapt content for platforms, preview posts, and prepare publishing.

The ArcSocial project stores reusable capabilities: agent skills, publishing
workflows, check scripts, templates, and platform adapters. User articles,
assets, platform drafts, publishing records, and metrics live in a separate data
workspace mounted as `workspace/` by default.

Chinese README: [README.md](README.md).

## Current Support

- General writing workflow: from raw ideas to canonical drafts, then to
  platform-specific drafts.
- WeChat Official Account: full adapter for local checks, preview generation,
  Wenyan-ready Markdown, and confirmed draft-box creation.
- Other social platforms: ArcSocial can generate platform-specific drafts. If a
  platform adapter does not exist, it stops at "platform draft ready" instead of
  pretending remote publishing is supported.

WeChat draft-box creation uses the open-source
[`wenyan-mcp`](https://github.com/caol64/wenyan-mcp) foundation. Follow its
official README for installation, `WECHAT_APP_ID` / `WECHAT_APP_SECRET`
configuration, IP whitelist requirements, local mode, and server mode.
ArcSocial does not store real secrets or access tokens.

## First-Time Setup

First prepare a personal data workspace. Recommended setup from the ArcSocial
project root:

```bash
node tools/scripts/init-workspace.mjs --repo <your-content-repo-url> --path workspace
node tools/scripts/doctor.mjs
```

If you do not have a personal content repository yet, create a local workspace
from the template:

```bash
node tools/scripts/init-workspace.mjs --new --path workspace
node tools/scripts/doctor.mjs
```

The default workspace path is configured in `arcsocial.config.json`:

```json
{
  "workspacePath": "workspace"
}
```

If you change the workspace path, keep `init-workspace.mjs --path` and
`arcsocial.config.json` aligned.

## Platform Configuration

After initialization, run `doctor`. It checks the workspace boundary, required
workspace directories, `wenyan-mcp`, `WECHAT_APP_ID`, and
`WECHAT_APP_SECRET`.

For WeChat Official Account publishing, configure credentials and IP whitelist
according to the `wenyan-mcp` README. Do not commit `WECHAT_APP_ID`,
`WECHAT_APP_SECRET`, `appsecret`, or `access_token` to Git.

## Daily Use

Users do not need to understand every project directory first. Tell the agent
what content you want to create, which platform you want to publish to, and what
stage you are at. The agent should create drafts, generate platform versions,
prepare previews, and stop for confirmation when needed.

Examples:

```text
Use ArcSocial to turn this idea into a WeChat Official Account article: ...
```

```text
Continue workspace/content/drafts/2026-06-23-example.md and prepare it for WeChat.
```

```text
Check whether this WeChat draft is ready to publish and generate a local preview.
```

```text
Adapt this canonical draft for X and WeChat.
```

## Project Boundary

This repository is the ArcSocial open-source project itself.

- `.agents/skills/` stores reusable agent skills.
- `arckit/` stores this project's ArcKit governance artifacts and project
  memory. It is part of the open-source project, not user content data.
- `docs/`, `playbooks/`, `skills/`, and `tools/` document and support reusable
  workflows.
- `templates/workspace/` contains the clean starter template for personal data
  repositories.
- `workspace/` is the recommended personal data mount point, usually as a Git
  submodule. It is not part of the ArcSocial open-source project itself.

User content should live in any independent Git repository mounted into
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

The internal structure of `workspace/` is an agent read/write contract. Users
usually do not need to memorize it; inspect `templates/workspace/` only when
debugging or doing manual maintenance.

## Naming

Use date-first names for content files:

```text
YYYY-MM-DD-topic.md
```
