# Desktop Writing Client

## Status

- State: parked
- Type: workflow
- Source: agent conversation
- Created: 2026-05-25
- Updated: 2026-05-25
- Decision: record only; do not execute yet

## Background

This repository is intended to support social media content operations: capturing personal ideas, collecting materials, writing drafts, adapting content for multiple platforms, and later using agents to process or improve content.

The idea came up because the current writing workflow has several open gaps:

- There is no dedicated place or interface for writing.
- After writing, it is unclear how content should land in this repository.
- Future agent-based processing needs predictable content files and workflow boundaries.

## Pending Item

Consider whether to build a desktop client for writing and managing content in this repository.

Possible responsibilities:

- Provide a low-friction writing entry point.
- Save drafts directly into the repository structure.
- Apply naming and template conventions automatically.
- Show content states such as inbox, draft, ready, and published.
- Trigger agent workflows for rewriting, platform adaptation, or review.

## Current Judgment

Do not build the desktop client yet.

The immediate need is likely better solved by a simpler workflow:

- Use Markdown files as the source of truth.
- Write directly in the repository with an existing editor.
- Add small scripts or commands for creating ideas, drafts, and platform adaptations.
- Let agents operate on those structured files first.

Building a client too early may add complexity before the actual workflow is proven.

## Revisit When

- Creating and moving Markdown files becomes repetitive enough to slow down daily use.
- There are many active drafts across multiple platforms.
- Agent workflows are stable and need a UI wrapper.
- The desired client behavior is clear from repeated manual usage.

## Related Areas

- `inbox/ideas/`
- `content/drafts/`
- `platforms/`
- `tools/`
- `skills/`

## Notes

- Open question: is the current problem mainly writing friction, file placement, or agent workflow orchestration?
- Open question: would a small CLI or script be enough before creating a desktop client?

## Outcome

Filled when promoted, merged, or closed.
