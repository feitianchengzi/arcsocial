# Wenyan MCP Foundation

Use `wenyan-mcp` as the preferred bottom layer for WeChat Official Account draft creation.

## Why This Foundation

Wenyan is already designed for AI-assisted Markdown publishing:

- Markdown to WeChat rich-text rendering.
- Built-in themes and custom themes.
- Local and remote image handling.
- WeChat draft-box publishing.
- Local MCP mode and remote server mode.
- Multi-platform direction beyond WeChat.

## Responsibility Split

`wenyan-mcp` owns:

- installation and runtime requirements.
- credential format and storage expectations.
- `WECHAT_APP_ID`, `WECHAT_APP_SECRET`, server URL, API key, and IP whitelist requirements.
- final Markdown rendering.
- image upload and replacement.
- cover handling.
- WeChat draft creation.

This skill owns:

- choosing the source file from this repository.
- adapting repository Markdown into the shape Wenyan expects.
- maintaining `arckit/publishing/` artifacts and non-secret result notes.
- checking readiness before a remote write.
- preserving the larger multi-platform publishing contract.

## Invocation Guidance

Install command documented by Wenyan:

```bash
npm install -g @wenyan-md/mcp
```

Before installing, check `node --version` and `npm --version`. Installation changes the user's global npm environment and may require network access, so ask before running it.

When `wenyan-mcp` is available as an MCP tool, use the MCP tool directly.

When only the local command is available, follow Wenyan's current documentation. Do not invent flags. If the installed version and this reference conflict, inspect `wenyan-mcp --help` or the project README and follow the installed version.

## Repository Mapping

Wenyan expects article metadata near the Markdown source as frontmatter. If the source is an existing `<workspacePath>/platforms/wechat/*.md` adaptation, create a generated Wenyan-ready Markdown file under `<workspacePath>/publishing/wechat/` if needed.

Documented fields:

```yaml
---
title: Article title
cover: /path/or/url/to/cover.jpg
author: Author name
source_url: https://example.com
need_open_comment: 0
only_fans_can_comment: 0
---
```

For image-message publishing, Wenyan also documents:

```yaml
---
title: Image article title
type: image
image_list:
  - ./1.jpeg
  - ./2.jpeg
---
```

`title` is required. `cover` may be a local path or URL; if absent, Wenyan can use the first body image as the cover. Wenyan handles supported body images, including absolute local paths, relative paths, and remote URLs.

Do not write Wenyan credentials into the generated file.

## Result Recording

After a successful draft creation, write a non-secret summary under:

```text
<workspacePath>/publishing/wechat/YYYY-MM-DD-slug.wenyan-result.md
```

Include:

- source file
- Wenyan mode used
- theme, if known
- draft media id, if returned
- manual review reminder
