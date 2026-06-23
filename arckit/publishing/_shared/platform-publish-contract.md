# Platform Publish Contract

## Purpose

Keep social publishing automation extensible across platforms without mixing writing, rendering, and API transport.

## Shared Model

- `SourceDraft`: canonical or platform-specific Markdown source.
- `PlatformAdaptation`: human-editable platform copy and metadata.
- `RenderedArtifact`: HTML, text, image manifest, or other platform-ready rendering.
- `PublishPayload`: exact request body or upload manifest used for an API call.
- `PublishResult`: non-secret API response summary and local audit record.

## Boundaries

- Repository files may store source, previews, payloads, reports, and non-secret API results.
- User-level Agent files store secrets and token caches.
- Platform adapters or selected foundations own platform limits, field mapping, rendering style, and upload rules.
- Publishing commands must have an explicit preview step before any remote write.
