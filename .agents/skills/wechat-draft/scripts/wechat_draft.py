#!/usr/bin/env python3
"""Prepare WeChat Official Account drafts through Wenyan.

This script intentionally uses only the Python standard library so the skill can
travel between projects with minimal setup.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CONFIG_FILE = Path("arcsocial.config.json")
DEFAULT_WORKSPACE_DIR = Path("workspace")
USER_DIR = Path.home() / ".arckit" / "AgentWorkspace" / "arcsocial" / "wechat"
CODEX_CONFIG_FILE = Path.home() / ".codex" / "config.toml"
BULLET_PARAGRAPH_STYLE = "margin: 0 0 8px; line-height: 1.75; color: #334155;"


def load_workspace_dir() -> Path:
    if not CONFIG_FILE.exists():
        return DEFAULT_WORKSPACE_DIR
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return DEFAULT_WORKSPACE_DIR
    value = data.get("workspacePath") or str(DEFAULT_WORKSPACE_DIR)
    return Path(value)


WORKSPACE_DIR = load_workspace_dir()
PUBLISH_DIR = WORKSPACE_DIR / "publishing" / "wechat"


def data_path(*parts: str) -> Path:
    return WORKSPACE_DIR.joinpath(*parts)


@dataclass
class Article:
    source: Path
    slug: str
    article_type: str
    title: str
    author: str
    digest: str
    content_markdown: str
    content_html: str
    content_source_url: str
    cover: str
    image_list: list[str]
    thumb_media_id: str
    show_cover_pic: int
    need_open_comment: int
    only_fans_can_comment: int
    style_reference: str
    content_change_scope: str
    warnings: list[str]


@dataclass
class AssetNote:
    label: str
    asset_path: str
    prompt_path: Path
    content: str


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"file not found: {path}")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def slug_for(path: Path) -> str:
    return path.stem


def section(text: str, heading: str) -> str:
    pattern = re.compile(rf"^## {re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return ""
    start = match.end()
    if heading == "Adapted Copy":
        next_match = re.search(r"^## (Assets|Publish Metadata|Post-Publish Notes)\s*$", text[start:], re.MULTILINE)
    else:
        next_match = re.search(r"^## .+$", text[start:], re.MULTILINE)
    end = start + next_match.start() if next_match else len(text)
    return text[start:end].strip()


def parse_metadata(block: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- ") or ":" not in stripped:
            continue
        key, value = stripped[2:].split(":", 1)
        metadata[normalize_key(key)] = value.strip()
    return metadata


def parse_list_value(value: str) -> list[str]:
    if not value:
        return []
    stripped = value.strip()
    if stripped.startswith("["):
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            parsed = []
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
    return [part.strip() for part in re.split(r"[,;，；]", stripped) if part.strip()]


def parse_toml_string(value: str) -> str:
    trimmed = value.strip()
    if trimmed.startswith('"') and trimmed.endswith('"'):
        return json.loads(trimmed)
    return trimmed


def load_codex_mcp_env(server_name: str = "wenyan") -> dict[str, str]:
    if not CODEX_CONFIG_FILE.exists():
        return {}
    target = f"mcp_servers.{server_name}.env"
    section = ""
    env: dict[str, str] = {}
    for raw_line in CODEX_CONFIG_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        header = re.match(r"^\[(.+)]$", line)
        if header:
            section = header.group(1)
            continue
        if section != target or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = parse_toml_string(value)
    return env


def relative_to_publish_dir(path_text: str) -> str:
    if not path_text:
        return ""
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", path_text):
        return path_text
    source_path = Path(path_text)
    if source_path.is_absolute() and source_path.exists():
        try:
            return os.path.relpath(source_path, PUBLISH_DIR)
        except ValueError:
            return path_text
    workspace_path = WORKSPACE_DIR / source_path
    if not source_path.is_absolute() and workspace_path.exists():
        try:
            return os.path.relpath(workspace_path, PUBLISH_DIR)
        except ValueError:
            return path_text
    if not source_path.exists():
        return path_text
    try:
        return os.path.relpath(source_path, PUBLISH_DIR)
    except ValueError:
        return path_text


def is_url(path_text: str) -> bool:
    return bool(re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", path_text))


def resolve_local_asset(path_text: str, source: Path) -> Path | None:
    if not path_text or is_url(path_text):
        return None
    path = Path(path_text)
    candidates = [path]
    if not path.is_absolute():
        candidates.append(WORKSPACE_DIR / path)
        candidates.append(source.parent / path)
        candidates.append(PUBLISH_DIR / path)
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return None


def image_refs(markdown: str) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    for match in re.finditer(r"!\[([^\]]*)\]\(([^)]+)\)", markdown):
        refs.append((match.group(1), match.group(2)))
    return refs


def normalize_asset_ref(path_text: str, source: Path) -> str:
    resolved = resolve_local_asset(path_text, source)
    if not resolved:
        return path_text
    return relative_to_publish_dir(str(resolved))


def normalize_markdown_image_paths(markdown: str, source: Path) -> str:
    def replace(match: re.Match[str]) -> str:
        alt, src = match.groups()
        resolved = resolve_local_asset(src, source)
        if not resolved:
            return match.group(0)
        return f"![{alt}]({relative_to_publish_dir(str(resolved))})"

    return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", replace, markdown)


def remove_markdown_images(markdown: str) -> str:
    lines = []
    for line in markdown.splitlines():
        if re.match(r"^\s*!\[[^\]]*\]\([^)]+\)\s*$", line):
            continue
        lines.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def plain_text_from_markdown(markdown: str) -> str:
    plain = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", markdown)
    plain = re.sub(r"^#+\s*", "", plain, flags=re.MULTILINE)
    plain = re.sub(r"[`*_>#-]", "", plain)
    return re.sub(r"\s+", " ", plain).strip()


def prompt_sidecar_for(path_text: str, source: Path) -> Path | None:
    resolved = resolve_local_asset(path_text, source)
    if not resolved:
        return None
    prompt_path = resolved.with_suffix(".prompt.md")
    if prompt_path.exists():
        return prompt_path
    return None


def asset_notes(article: Article) -> list[AssetNote]:
    notes: list[AssetNote] = []
    seen: set[Path] = set()
    candidates = [("cover", article.cover)]
    candidates.extend((alt or "body image", src) for alt, src in image_refs(article.content_markdown))
    candidates.extend(("image message", src) for src in article.image_list)
    for label, path_text in candidates:
        prompt_path = prompt_sidecar_for(path_text, article.source)
        if not prompt_path or prompt_path in seen:
            continue
        seen.add(prompt_path)
        notes.append(
            AssetNote(
                label=label,
                asset_path=path_text,
                prompt_path=prompt_path,
                content=read_text(prompt_path).strip(),
            )
        )
    return notes


def normalize_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", key.strip().lower()).strip("_")


def parse_int(value: str, default: int) -> int:
    if value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def first_heading(markdown: str) -> str:
    for line in markdown.splitlines():
        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match:
            return match.group(1).strip()
    return ""


def strip_first_h1(markdown: str) -> str:
    lines = markdown.splitlines()
    if lines and re.match(r"^#\s+", lines[0]):
        return "\n".join(lines[1:]).strip()
    return markdown.strip()


def inline_markup(text: str) -> str:
    escaped = html.escape(text, quote=False)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", escaped)
    return escaped


def bullet_paragraph(text: str) -> str:
    return f'<p style="{BULLET_PARAGRAPH_STYLE}">• {inline_markup(text.strip())}</p>'


def normalize_wechat_lists(markdown: str) -> tuple[str, list[str]]:
    warnings: list[str] = []
    html_items_converted = 0

    def convert_html_list(match: re.Match[str]) -> str:
        nonlocal html_items_converted
        inner = match.group(1)
        items = re.findall(r"<li\b[^>]*>(.*?)</li>", inner, flags=re.IGNORECASE | re.DOTALL)
        if not items:
            return match.group(0)
        html_items_converted += len(items)
        paragraphs = []
        for item in items:
            compact = re.sub(r"\s+", " ", item).strip()
            paragraphs.append(bullet_paragraph(compact))
        return "\n".join(paragraphs)

    normalized = re.sub(
        r"<ul\b[^>]*>(.*?)</ul>",
        convert_html_list,
        markdown,
        flags=re.IGNORECASE | re.DOTALL,
    )

    markdown_items_converted = 0
    lines: list[str] = []
    for raw_line in normalized.splitlines():
        bullet = re.match(r"^[-*]\s+(.+?)\s*$", raw_line)
        if bullet:
            markdown_items_converted += 1
            lines.append(bullet_paragraph(bullet.group(1)))
        else:
            lines.append(raw_line)
    normalized = "\n".join(lines).strip()

    if html_items_converted:
        warnings.append(
            f"converted {html_items_converted} HTML list item(s) to bullet paragraphs to avoid blank list items in WeChat drafts."
        )
    if markdown_items_converted:
        warnings.append(
            f"converted {markdown_items_converted} Markdown list item(s) to bullet paragraphs to avoid blank list items in WeChat drafts."
        )
    if re.search(r"</?(ul|li)\b", normalized, flags=re.IGNORECASE):
        warnings.append("content still contains <ul>/<li>; WeChat draft may show blank list items.")

    return normalized, warnings


def latest_style_reference(source: Path) -> str:
    candidates: list[tuple[float, Path]] = []
    platform_dir = data_path("platforms", "wechat")
    source_resolved = source.resolve()

    for result_path in PUBLISH_DIR.glob("*.wenyan-result.md"):
        slug = result_path.name.removesuffix(".wenyan-result.md")
        candidate = platform_dir / f"{slug}.md"
        if candidate.exists() and candidate.resolve() != source_resolved:
            candidates.append((result_path.stat().st_mtime, candidate))

    if not candidates:
        if platform_dir.exists():
            for candidate in platform_dir.glob("*.md"):
                if candidate.resolve() != source_resolved:
                    candidates.append((candidate.stat().st_mtime, candidate))

    if not candidates:
        return ""

    candidates.sort(key=lambda item: item[0], reverse=True)
    return str(candidates[0][1])


def markdown_to_wechat_html(markdown: str) -> str:
    blocks: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    quote_lines: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            text = " ".join(line.strip() for line in paragraph).strip()
            blocks.append(
                '<p style="margin: 0 0 18px; line-height: 1.8; font-size: 16px; color: #1f2933;">'
                + inline_markup(text)
                + "</p>"
            )
            paragraph = []

    def flush_list() -> None:
        nonlocal list_items
        if list_items:
            blocks.extend(bullet_paragraph(item) for item in list_items)
            list_items = []

    def flush_quote() -> None:
        nonlocal quote_lines
        if quote_lines:
            text = "<br>".join(inline_markup(line) for line in quote_lines)
            blocks.append(
                '<blockquote style="margin: 20px 0; padding: 10px 14px; border-left: 4px solid #d0d7de; color: #57606a; background: #f6f8fa; line-height: 1.8;">'
                + text
                + "</blockquote>"
            )
            quote_lines = []

    for raw_line in strip_first_h1(markdown).splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            flush_list()
            flush_quote()
            continue
        image = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", stripped)
        heading = re.match(r"^(#{2,4})\s+(.+)$", stripped)
        bullet = re.match(r"^[-*]\s+(.+)$", stripped)
        quote = re.match(r"^>\s*(.+)$", stripped)
        if image:
            flush_paragraph()
            flush_list()
            flush_quote()
            alt, src = image.groups()
            blocks.append(
                '<p style="margin: 22px 0; text-align: center;">'
                f'<img src="{html.escape(src, quote=True)}" alt="{html.escape(alt, quote=True)}" style="max-width: 100%; height: auto;" />'
                "</p>"
            )
        elif heading:
            flush_paragraph()
            flush_list()
            flush_quote()
            blocks.append(
                '<h2 style="margin: 28px 0 14px; line-height: 1.45; font-size: 20px; font-weight: 700; color: #111827;">'
                + inline_markup(heading.group(2).strip())
                + "</h2>"
            )
        elif bullet:
            flush_paragraph()
            flush_quote()
            list_items.append(bullet.group(1).strip())
        elif quote:
            flush_paragraph()
            flush_list()
            quote_lines.append(quote.group(1).strip())
        elif stripped.startswith("<"):
            flush_paragraph()
            flush_list()
            flush_quote()
            blocks.append(stripped)
        else:
            flush_list()
            flush_quote()
            paragraph.append(stripped)

    flush_paragraph()
    flush_list()
    flush_quote()
    return "\n".join(blocks)


def build_article(source: Path) -> Article:
    text = read_text(source)
    adapted = section(text, "Adapted Copy")
    if not adapted:
        adapted = text.strip()
    adapted = normalize_markdown_image_paths(adapted, source)
    adapted, list_warnings = normalize_wechat_lists(adapted)
    metadata = parse_metadata(section(text, "Publish Metadata"))
    warnings: list[str] = list_warnings

    raw_type = metadata.get("type") or metadata.get("article_type") or metadata.get("content_type", "")
    article_type = "image" if raw_type.lower() in {"image", "newspic", "图片", "图片消息", "小绿书"} else "news"
    title = metadata.get("title") or first_heading(adapted) or first_heading(text) or source.stem
    author = metadata.get("author", "")
    digest = metadata.get("digest") or metadata.get("caption", "")
    content_source_url = metadata.get("content_source_url", "")
    cover = metadata.get("cover") or metadata.get("cover_url") or metadata.get("cover_path", "")
    explicit_image_list = parse_list_value(metadata.get("image_list", metadata.get("images", "")))
    image_list = [normalize_asset_ref(item, source) for item in explicit_image_list]
    if article_type == "image" and not image_list:
        image_list = [src for _, src in image_refs(adapted)]
    content_markdown = remove_markdown_images(adapted) if article_type == "image" else adapted
    thumb_media_id = metadata.get("cover_media_id") or metadata.get("thumb_media_id", "")
    show_cover_pic = parse_int(metadata.get("show_cover", metadata.get("show_cover_pic", "0")), 0)
    need_open_comment = parse_int(metadata.get("need_open_comment", "0"), 0)
    only_fans_can_comment = parse_int(metadata.get("only_fans_can_comment", "0"), 0)
    content_html = markdown_to_wechat_html(content_markdown)
    style_reference = latest_style_reference(source)
    content_change_scope = "publishing-safety"

    if article_type == "image":
        if not image_list:
            warnings.append("missing image_list: Wenyan image messages require images in body or Publish Metadata Image List.")
        if len(image_list) > 20:
            warnings.append(f"image_list has {len(image_list)} images; Wenyan image messages support at most 20.")
        if len(title) > 20:
            warnings.append(f"image message title exceeds 20 characters: {len(title)} characters.")
        if not cover and image_list:
            cover = image_list[0]
        body_plain = plain_text_from_markdown(content_markdown)
        if len(body_plain) < 80:
            warnings.append("image message lower body is very short; make sure it is reader-facing and adds value beyond describing the draft.")
        if re.search(r"(草稿|用\s*\d+\s*张图|这是一版)", body_plain):
            warnings.append("image message lower body may be creator-facing; rewrite it for the public reader and the post objective.")
    elif not cover and not thumb_media_id:
        warnings.append("missing cover: Wenyan requires a cover image or at least one body image.")
    if article_type != "image" and not digest:
        warnings.append("missing digest: do not rely on WeChat defaults for final copy.")
    if len(title) > 64:
        warnings.append(f"title may be too long for WeChat conventions: {len(title)} characters.")
    if len(digest) > 120:
        warnings.append(f"digest may be too long: {len(digest)} characters.")
    if len(content_html.encode("utf-8")) > 1024 * 1024:
        warnings.append("content HTML is larger than 1MB.")
    if re.search(r'<img src="(?!https?://)', content_html):
        if article_type == "image":
            warnings.append("image message contains local image paths; Wenyan should upload them and produce image media ids.")
        else:
            warnings.append("content contains local body image paths; Wenyan should upload them, but the fallback direct API payload would need WeChat-hosted image URLs.")
    if re.search(r'<img src="https?://', content_html):
        warnings.append("content contains remote image URLs; WeChat may filter non-WeChat image hosts.")

    return Article(
        source=source,
        slug=slug_for(source),
        article_type=article_type,
        title=title,
        author=author,
        digest=digest,
        content_markdown=content_markdown,
        content_html=content_html,
        content_source_url=content_source_url,
        cover=cover,
        image_list=image_list,
        thumb_media_id=thumb_media_id,
        show_cover_pic=show_cover_pic,
        need_open_comment=need_open_comment,
        only_fans_can_comment=only_fans_can_comment,
        style_reference=style_reference,
        content_change_scope=content_change_scope,
        warnings=warnings,
    )


def suggested_digest(article: Article) -> str:
    if article.digest:
        return article.digest
    plain = re.sub(r"^# .+$", "", article.content_markdown, flags=re.MULTILINE)
    plain = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", plain)
    plain = re.sub(r"[`*_>#-]", "", plain)
    plain = re.sub(r"\s+", " ", plain).strip()
    if len(plain) <= 96:
        return plain
    return plain[:96].rstrip("，。；、 ") + "..."


def payload_for(article: Article) -> dict[str, Any]:
    if article.article_type == "image":
        item = {
            "article_type": "newspic",
            "title": article.title,
            "content": article.content_html,
            "need_open_comment": article.need_open_comment,
            "only_fans_can_comment": article.only_fans_can_comment,
            "image_info": {
                "image_list": [
                    {
                        "image_media_id": "",
                        "_source_path": src,
                    }
                    for src in article.image_list
                ]
            },
        }
        return {"articles": [item]}

    item = {
        "article_type": "news",
        "title": article.title,
        "author": article.author,
        "digest": article.digest,
        "content": article.content_html,
        "content_source_url": article.content_source_url,
        "thumb_media_id": article.thumb_media_id,
        "show_cover_pic": article.show_cover_pic,
        "need_open_comment": article.need_open_comment,
        "only_fans_can_comment": article.only_fans_can_comment,
    }
    return {"articles": [item]}


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    data: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        try:
            data[key] = json.loads(value)
        except json.JSONDecodeError:
            data[key] = value.strip('"')
    return data


def apply_cover_override(article: Article, cover: str) -> None:
    if not cover:
        return
    article.cover = cover
    article.warnings = [warning for warning in article.warnings if not warning.startswith("missing cover:")]


def infer_existing_wenyan_cover(article: Article) -> str:
    path = PUBLISH_DIR / f"{article.slug}.wenyan.md"
    if not path.exists():
        return ""
    metadata = parse_frontmatter(read_text(path))
    cover = metadata.get("cover", "")
    if not cover:
        return ""
    cover_path = Path(cover)
    if cover_path.is_absolute() or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", cover):
        return cover
    return str((path.parent / cover_path).resolve())


def resolve_preview_asset(path_text: str) -> str:
    if not path_text:
        return ""
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", path_text):
        return path_text
    p = Path(path_text)
    candidates = [p]
    if not p.is_absolute():
        candidates = [
            PUBLISH_DIR / p,
            WORKSPACE_DIR / p,
            Path.cwd() / p,
        ]
    for candidate in candidates:
        if candidate.exists():
            try:
                return os.path.relpath(candidate.resolve(), PUBLISH_DIR)
            except ValueError:
                return str(candidate)
    if p.is_absolute():
        try:
            return os.path.relpath(p, PUBLISH_DIR)
        except ValueError:
            return str(p)
    return path_text


def platform_api_fields(article: Article) -> list[tuple[str, str, str]]:
    if article.article_type == "image":
        return [
            ("article_type", "newspic", "WeChat draft/add image-message article type"),
            ("title", article.title, "from Publish Metadata Title or first H1"),
            ("content", f"HTML {len(article.content_html)} chars / {len(article.content_html.encode('utf-8'))} bytes", "image message description/content"),
            ("image_list", f"{len(article.image_list)} image(s)", "Wenyan uploads these images; fallback payload shows source paths"),
            ("need_open_comment", str(article.need_open_comment), "Wenyan frontmatter/direct API"),
            ("only_fans_can_comment", str(article.only_fans_can_comment), "Wenyan frontmatter/direct API"),
            ("cover", article.cover, "first image by default unless explicitly set"),
        ]

    return [
        ("article_type", "news", "WeChat draft/add article type"),
        ("title", article.title, "from Publish Metadata Title or first H1"),
        ("author", article.author, "optional"),
        ("digest", article.digest, "from Publish Metadata Digest/Caption"),
        ("content", f"HTML {len(article.content_html)} chars / {len(article.content_html.encode('utf-8'))} bytes", "fallback preview HTML; Wenyan renders final HTML"),
        ("content_source_url", article.content_source_url, "optional original link"),
        ("thumb_media_id", article.thumb_media_id, "fallback direct API only; Wenyan uses cover path/URL"),
        ("show_cover_pic", str(article.show_cover_pic), "fallback direct API only"),
        ("need_open_comment", str(article.need_open_comment), "Wenyan frontmatter/direct API"),
        ("only_fans_can_comment", str(article.only_fans_can_comment), "Wenyan frontmatter/direct API"),
        ("cover", article.cover, "Wenyan frontmatter local path or URL"),
    ]


def full_preview_html(article: Article, wenyan_path: Path, fallback_payload_path: Path, report_path: Path) -> str:
    if article.article_type == "image":
        return image_message_preview_html(article, wenyan_path, fallback_payload_path, report_path)

    cover_src = resolve_preview_asset(article.cover)
    cover_html = (
        f'<img class="cover" src="{html.escape(cover_src, quote=True)}" alt="cover" />'
        if cover_src
        else '<div class="missing-cover">No cover configured</div>'
    )
    rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(name)}</td>"
        f"<td>{html.escape(value or '(empty)')}</td>"
        f"<td>{html.escape(note)}</td>"
        "</tr>"
        for name, value, note in platform_api_fields(article)
    )
    note_blocks = "\n".join(
        '<details class="asset-note">'
        f"<summary>{html.escape(note.label)}: {html.escape(note.asset_path)}</summary>"
        f"<div class=\"note-path\">{html.escape(str(note.prompt_path))}</div>"
        f"<pre>{html.escape(note.content)}</pre>"
        "</details>"
        for note in asset_notes(article)
    )
    notes_html = (
        f"<section><h2>Image Generation Notes</h2>{note_blocks}</section>"
        if note_blocks
        else ""
    )
    escaped_wenyan = html.escape(str(wenyan_path))
    escaped_payload = html.escape(str(fallback_payload_path))
    escaped_report = html.escape(str(report_path))
    escaped_style_reference = html.escape(article.style_reference or "none found")
    escaped_change_scope = html.escape(article.content_change_scope)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(article.title)} - WeChat Preview</title>
  <style>
    body {{ margin: 0; background: #eef1f5; color: #1f2933; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    main {{ max-width: 1040px; margin: 0 auto; padding: 28px 18px 56px; }}
    section {{ margin: 0 0 28px; }}
    .article {{ max-width: 720px; background: #fff; padding: 28px 22px 40px; }}
    .cover {{ display: block; width: 100%; max-width: 720px; aspect-ratio: 1.8 / 1; object-fit: cover; background: #d8dee8; }}
    .missing-cover {{ width: 100%; max-width: 720px; aspect-ratio: 1.8 / 1; display: grid; place-items: center; color: #6b7280; background: #dde3eb; }}
    h1 {{ margin: 18px 0 10px; font-size: 26px; line-height: 1.35; }}
    h2 {{ margin: 0 0 12px; font-size: 18px; }}
    .digest {{ margin: 12px 0 24px; padding: 12px 14px; background: #f8fafc; color: #4b5563; line-height: 1.7; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; font-size: 14px; }}
    th, td {{ border: 1px solid #d7dde5; padding: 9px 10px; text-align: left; vertical-align: top; }}
    th {{ background: #f6f8fb; }}
    code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
    .paths {{ color: #4b5563; line-height: 1.7; font-size: 14px; }}
    .asset-note {{ margin: 0 0 12px; background: #fff; border: 1px solid #d7dde5; }}
    .asset-note summary {{ cursor: pointer; padding: 10px 12px; font-weight: 600; }}
    .note-path {{ padding: 0 12px 8px; color: #6b7280; font-size: 13px; }}
    .asset-note pre {{ margin: 0; padding: 12px; white-space: pre-wrap; background: #f8fafc; border-top: 1px solid #d7dde5; line-height: 1.55; }}
  </style>
</head>
<body>
  <main>
    <section>
      <h2>Preview Artifacts</h2>
      <div class="paths">
        Wenyan input: <code>{escaped_wenyan}</code><br>
        Fallback payload: <code>{escaped_payload}</code><br>
        Report: <code>{escaped_report}</code>
      </div>
    </section>
    <section>
      <h2>Publishing Style Pass</h2>
      <div class="paths">
        Style reference: <code>{escaped_style_reference}</code><br>
        Content change scope: <code>{escaped_change_scope}</code>
      </div>
    </section>
    <section>
      <h2>WeChat / Wenyan Fields</h2>
      <table>
        <thead><tr><th>Field</th><th>Actual value</th><th>Source / note</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </section>
    {notes_html}
    <section class="article">
      {cover_html}
      <h1>{html.escape(article.title)}</h1>
      <div class="digest">{html.escape(article.digest or "未设置摘要")}</div>
      {article.content_html}
    </section>
  </main>
</body>
</html>
"""


def image_message_preview_html(
    article: Article,
    wenyan_path: Path,
    fallback_payload_path: Path,
    report_path: Path,
) -> str:
    rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(name)}</td>"
        f"<td>{html.escape(value or '(empty)')}</td>"
        f"<td>{html.escape(note)}</td>"
        "</tr>"
        for name, value, note in platform_api_fields(article)
    )
    note_blocks = "\n".join(
        '<details class="asset-note">'
        f"<summary>{html.escape(note.label)}: {html.escape(note.asset_path)}</summary>"
        f"<div class=\"note-path\">{html.escape(str(note.prompt_path))}</div>"
        f"<pre>{html.escape(note.content)}</pre>"
        "</details>"
        for note in asset_notes(article)
    )
    notes_html = (
        f"<section><h2>Image Generation Notes</h2>{note_blocks}</section>"
        if note_blocks
        else ""
    )
    slides = "\n".join(
        '<figure class="slide">'
        f'<img src="{html.escape(resolve_preview_asset(src), quote=True)}" alt="image message {index}" />'
        f"<figcaption>{index} / {len(article.image_list)}</figcaption>"
        "</figure>"
        for index, src in enumerate(article.image_list, start=1)
    )
    if not slides:
        slides = '<div class="missing-images">No image_list configured</div>'
    cover_audit = " / ".join(
        [
            "type=image",
            f"image_list={len(article.image_list)}",
            "standalone cover not emitted to Wenyan",
            f"first image cover={article.image_list[0] if article.image_list else '(missing)'}",
        ]
    )
    escaped_wenyan = html.escape(str(wenyan_path))
    escaped_payload = html.escape(str(fallback_payload_path))
    escaped_report = html.escape(str(report_path))
    escaped_style_reference = html.escape(article.style_reference or "none found")
    escaped_change_scope = html.escape(article.content_change_scope)
    escaped_cover_audit = html.escape(cover_audit)
    lower_body = article.content_html or '<p class="empty-body">No lower body configured</p>'
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(article.title)} - WeChat Image Message Preview</title>
  <style>
    body {{ margin: 0; background: #e8edf2; color: #1f2933; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 28px 18px 56px; }}
    .layout {{ display: grid; grid-template-columns: minmax(330px, 420px) minmax(0, 1fr); gap: 28px; align-items: start; }}
    .phone {{ border: 1px solid #cfd7e2; background: #f6f8fb; border-radius: 28px; padding: 12px; box-shadow: 0 18px 50px rgba(15, 23, 42, 0.16); }}
    .screen {{ overflow: hidden; border-radius: 22px; background: #fff; min-height: 720px; }}
    .topbar {{ height: 44px; display: flex; align-items: center; justify-content: center; border-bottom: 1px solid #eef1f5; font-size: 14px; font-weight: 600; color: #111827; }}
    .carousel {{ display: flex; overflow-x: auto; scroll-snap-type: x mandatory; -webkit-overflow-scrolling: touch; background: #111827; }}
    .slide {{ position: relative; flex: 0 0 100%; margin: 0; scroll-snap-align: start; aspect-ratio: 3 / 4; background: #111827; }}
    .slide img {{ display: block; width: 100%; height: 100%; object-fit: contain; }}
    .slide figcaption {{ position: absolute; right: 12px; bottom: 12px; padding: 3px 8px; border-radius: 999px; background: rgba(17, 24, 39, 0.72); color: #fff; font-size: 12px; }}
    .fixed-body {{ padding: 20px 18px 28px; border-top: 1px solid #eef1f5; }}
    .fixed-body h1 {{ margin: 0 0 14px; font-size: 21px; line-height: 1.35; letter-spacing: 0; }}
    .fixed-body p {{ font-size: 15px !important; line-height: 1.75 !important; color: #1f2933 !important; }}
    .fixed-body blockquote {{ font-size: 15px !important; }}
    .empty-body, .missing-images {{ padding: 24px; color: #6b7280; text-align: center; }}
    section {{ margin: 0 0 24px; }}
    h2 {{ margin: 0 0 12px; font-size: 18px; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; font-size: 14px; }}
    th, td {{ border: 1px solid #d7dde5; padding: 9px 10px; text-align: left; vertical-align: top; }}
    th {{ background: #f6f8fb; }}
    code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
    .paths {{ color: #4b5563; line-height: 1.7; font-size: 14px; background: #fff; border: 1px solid #d7dde5; padding: 12px 14px; }}
    .audit {{ margin: 0 0 14px; padding: 10px 12px; background: #fff7ed; border: 1px solid #fed7aa; color: #7c2d12; line-height: 1.6; font-size: 14px; }}
    .asset-note {{ margin: 0 0 12px; background: #fff; border: 1px solid #d7dde5; }}
    .asset-note summary {{ cursor: pointer; padding: 10px 12px; font-weight: 600; }}
    .note-path {{ padding: 0 12px 8px; color: #6b7280; font-size: 13px; }}
    .asset-note pre {{ margin: 0; padding: 12px; white-space: pre-wrap; background: #f8fafc; border-top: 1px solid #d7dde5; line-height: 1.55; }}
    @media (max-width: 820px) {{
      main {{ padding: 16px 10px 36px; }}
      .layout {{ grid-template-columns: 1fr; }}
      .phone {{ max-width: 420px; margin: 0 auto; }}
    }}
  </style>
</head>
<body>
  <main>
    <div class="layout">
      <section class="phone" aria-label="image message local preview">
        <div class="screen">
          <div class="topbar">公众号图片消息预览</div>
          <div class="carousel">{slides}</div>
          <article class="fixed-body">
            <h1>{html.escape(article.title)}</h1>
            {lower_body}
          </article>
        </div>
      </section>
      <div>
        <section>
          <h2>Preview Artifacts</h2>
          <div class="paths">
            Wenyan input: <code>{escaped_wenyan}</code><br>
            Fallback payload: <code>{escaped_payload}</code><br>
            Report: <code>{escaped_report}</code>
          </div>
        </section>
        <section>
          <h2>Image Message Audit</h2>
          <div class="audit">{escaped_cover_audit}</div>
          <table>
            <thead><tr><th>Field</th><th>Actual value</th><th>Source / note</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </section>
        <section>
          <h2>Publishing Style Pass</h2>
          <div class="paths">
            Style reference: <code>{escaped_style_reference}</code><br>
            Content change scope: <code>{escaped_change_scope}</code>
          </div>
        </section>
        {notes_html}
      </div>
    </div>
  </main>
</body>
</html>
"""


def report_markdown(
    article: Article,
    payload_path: Path,
    full_preview_path: Path | None = None,
) -> str:
    field_rows = "\n".join(
        f"| `{name}` | `{short_value(value or '(empty)')}` | {note} |"
        for name, value, note in platform_api_fields(article)
    )
    warnings = "\n".join(f"- {warning}" for warning in article.warnings) or "- none"
    suggestions = []
    if article.article_type != "image" and not article.digest:
        suggestions.append(f"- Digest: {suggested_digest(article)}")
    if article.article_type == "image" and not article.image_list:
        suggestions.append("- Image List: add body images or `- Image List:` under `## Publish Metadata`.")
    elif article.article_type != "image" and not article.cover and not article.thumb_media_id:
        suggestions.append("- Cover: provide a local cover path, remote cover URL, or body image.")
    suggested_block = "\n".join(suggestions) or "- none"
    full_preview_line = f"- Full Preview HTML: `{full_preview_path}`\n" if full_preview_path else ""
    if article.article_type == "image":
        preview_note = "- Full Preview HTML uses the image-message template: horizontal image list, fixed lower body, and field/cover audit."
    else:
        preview_note = "- Full Preview HTML shows the API/Wenyan field matrix, cover, digest, and rendered body together."
    notes = asset_notes(article)
    if notes:
        asset_note_block = "\n\n".join(
            f"### {note.label}: `{note.asset_path}`\n\n"
            f"- Prompt note: `{note.prompt_path}`\n\n"
            f"```text\n{note.content}\n```"
            for note in notes
        )
    else:
        asset_note_block = "- none"
    return f"""# WeChat Draft Preview Report

## Source

- Markdown: `{article.source}`
- Style Reference: `{article.style_reference or 'none found'}`
- Content Change Scope: `{article.content_change_scope}`
{full_preview_line}{preview_note}
- Fallback Payload JSON: `{payload_path}`

## Publishing Style Pass

- The preview pipeline automatically applies the WeChat publishing pass before rendering.
- Current deterministic pass: image path normalization, list-safety conversion, stable local preview/Wenyan output, and latest WeChat style reference discovery.
- Source modified: no.
- If a future agent performs light editorial style adaptation, it must keep that change in generated publishing artifacts and report the scope here.

## WeChat / Wenyan Fields

| Field | Actual value | Source / note |
|---|---|---|
{field_rows}

## Warnings

{warnings}

## Suggested Metadata

{suggested_block}

## Image Generation Notes

{asset_note_block}

## Manual Review

- Open the preview HTML locally.
- Check the generated `content` in the payload JSON.
- Confirm cover/body image before creating a remote draft.
- Inspect the final draft in the WeChat backend before publishing.
"""


def wenyan_frontmatter(article: Article) -> dict[str, Any]:
    data: dict[str, Any] = {"title": article.title}
    if article.article_type == "image":
        data["type"] = "image"
        if article.image_list:
            data["image_list"] = [relative_to_publish_dir(item) for item in article.image_list]
    if article.cover and article.article_type != "image":
        data["cover"] = relative_to_publish_dir(article.cover)
    if article.author:
        data["author"] = article.author
    if article.content_source_url:
        data["source_url"] = article.content_source_url
    if article.need_open_comment:
        data["need_open_comment"] = article.need_open_comment
    if article.only_fans_can_comment:
        data["only_fans_can_comment"] = article.only_fans_can_comment
    return data


def yaml_scalar(value: Any) -> str:
    if isinstance(value, list):
        return "\n" + "\n".join(f"  - {yaml_scalar(item)}" for item in value)
    if isinstance(value, int):
        return str(value)
    text = str(value)
    if re.match(r"^[A-Za-z0-9_./:-]+$", text):
        return text
    return json.dumps(text, ensure_ascii=False)


def content_markdown_for_wenyan(article: Article) -> str:
    content = article.content_markdown.strip()
    digest = article.digest.strip()
    if not digest or digest in content:
        return content

    digest_block = f"> {digest}"
    lines = content.splitlines()
    if lines and re.match(r"^#\s+", lines[0]):
        rest = lines[1:]
        while rest and not rest[0].strip():
            rest = rest[1:]
        return "\n".join([lines[0], "", digest_block, "", *rest]).strip()
    return f"{digest_block}\n\n{content}".strip()


def render_wenyan_markdown(article: Article) -> str:
    frontmatter = wenyan_frontmatter(article)
    lines = ["---"]
    for key, value in frontmatter.items():
        rendered = yaml_scalar(value)
        if rendered.startswith("\n"):
            lines.append(f"{key}:{rendered}")
        else:
            lines.append(f"{key}: {rendered}")
    lines.append("---")
    lines.append("")
    lines.append(content_markdown_for_wenyan(article))
    lines.append("")
    return "\n".join(lines)


def short_value(value: Any) -> str:
    text = str(value)
    if len(text) > 80:
        return text[:77] + "..."
    return text


def command_path(name: str) -> str:
    return shutil.which(name) or ""


def shell_version(command: str) -> str:
    path = command_path(command)
    if not path:
        return "missing"
    import subprocess

    try:
        result = subprocess.run(
            [command, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except OSError as exc:
        return f"error: {exc}"
    except subprocess.TimeoutExpired:
        return "error: version check timed out"
    version = (result.stdout or result.stderr).strip().splitlines()
    if result.returncode != 0:
        return f"error: exit {result.returncode}"
    return version[0] if version else path


def command_preview(args: argparse.Namespace) -> None:
    source = Path(args.source)
    article = build_article(source)
    cover = args.cover or infer_existing_wenyan_cover(article)
    apply_cover_override(article, cover)
    payload = payload_for(article)
    if args.dry_run:
        print(
            report_markdown(
                article,
                Path("<dry-run>.fallback-payload.json"),
                Path("<dry-run>.full-preview.html"),
            )
        )
        return
    PUBLISH_DIR.mkdir(parents=True, exist_ok=True)
    payload_path = PUBLISH_DIR / f"{article.slug}.fallback-payload.json"
    report_path = PUBLISH_DIR / f"{article.slug}.report.md"
    full_preview_path = PUBLISH_DIR / f"{article.slug}.full-preview.html"
    wenyan_path = PUBLISH_DIR / f"{article.slug}.wenyan.md"
    write_json(payload_path, payload)
    full_preview_path.write_text(full_preview_html(article, wenyan_path, payload_path, report_path), encoding="utf-8")
    report_path.write_text(report_markdown(article, payload_path, full_preview_path), encoding="utf-8")
    print(f"source: {source}")
    print(f"full_preview_html: {full_preview_path}")
    print(f"payload_json: {payload_path}")
    print(f"report: {report_path}")
    if article.warnings:
        print("warnings:")
        for warning in article.warnings:
            print(f"- {warning}")


def command_prepare_wenyan(args: argparse.Namespace) -> None:
    source = Path(args.source)
    article = build_article(source)
    apply_cover_override(article, args.cover)
    rendered = render_wenyan_markdown(article)
    output_path = PUBLISH_DIR / f"{article.slug}.wenyan.md"
    if args.dry_run:
        print(rendered)
        if article.warnings:
            print("Warnings:", file=sys.stderr)
            for warning in article.warnings:
                print(f"- {warning}", file=sys.stderr)
        if article.article_type != "image" and not article.digest:
            print(f"Suggested Digest: {suggested_digest(article)}", file=sys.stderr)
        return
    PUBLISH_DIR.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    print(f"source: {source}")
    print(f"wenyan_input: {output_path}")
    if article.warnings:
        print("warnings:")
        for warning in article.warnings:
            print(f"- {warning}")
    if article.article_type != "image" and not article.digest:
        print(f"suggested_digest: {suggested_digest(article)}")


def command_doctor(args: argparse.Namespace) -> None:
    print("WeChat draft setup check")
    print("")
    print("preferred_foundation: wenyan-mcp")
    print("")
    print("Environment:")
    print(f"- node: {shell_version('node')}")
    print(f"- npm: {shell_version('npm')}")
    wenyan_path = command_path("wenyan-mcp")
    codex_env = load_codex_mcp_env()
    merged_env = {**codex_env, **os.environ}
    if wenyan_path:
        print(f"- wenyan-mcp: {wenyan_path}")
    else:
        print("- wenyan-mcp: missing")
    print("")
    print("Wenyan setup:")
    if not command_path("npm"):
        print("- install npm/node before installing local wenyan-mcp")
    if not wenyan_path:
        print("- install local command when local mode is desired:")
        print("  npm install -g @wenyan-md/mcp")
    print(f"- WECHAT_APP_ID: {mask(merged_env.get('WECHAT_APP_ID', ''))}")
    print(f"- WECHAT_APP_SECRET: {'configured' if merged_env.get('WECHAT_APP_SECRET') else 'missing'}")
    if codex_env:
        print(f"- Codex MCP env: loaded from {CODEX_CONFIG_FILE}")
    print("- WeChat Official Account IP whitelist: verify in WeChat backend for local API mode")
    print("- Remote Wenyan server/API key: follow Wenyan docs if using remote mode")
    print("")
    print("Decision boundary:")
    print(f"- Agent may run check/preview and write generated artifacts under {PUBLISH_DIR}.")
    print("- Agent may generate suggested metadata in generated artifacts.")
    print("- Ask before installing global packages, entering secrets, editing source files, or creating a remote draft.")
    print("- Public publish is not supported by this skill.")
    print("")
    print("Before creating a real draft, the article source also needs:")
    print("- Title: from Publish Metadata or the first H1")
    print("- Digest: `- Digest:` under `## Publish Metadata`")
    print("- Cover: local path, remote URL, or Wenyan-supported cover metadata")
    print("- Image message: `- Type: image` plus body images or `- Image List:` under `## Publish Metadata`")
    print("- Cover quality: use a generated or user-provided bitmap; this script does not generate covers")
    print("- Content: `## Adapted Copy` body")
    print("")
    print("Recommended order:")
    print("1. Install/configure wenyan-mcp using its own docs.")
    print("2. Run this `doctor` command for repository-level readiness.")
    print("3. Run `preview` if you want a local fallback HTML/payload report.")
    print("4. Use wenyan-mcp for the real draft-box write.")
    print(f"5. Record non-secret results under `{PUBLISH_DIR}/`.")


def mask(value: str) -> str:
    if not value:
        return "missing"
    if len(value) <= 8:
        return value[:2] + "***"
    return value[:4] + "***" + value[-4:]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare WeChat Official Account drafts through Wenyan.")
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="show required setup and local configuration status")
    doctor.set_defaults(func=command_doctor)

    preview = sub.add_parser("preview", help="render local preview and draft API payload")
    preview.add_argument("source", help="workspace platforms/wechat/*.md source file")
    preview.add_argument("--cover", help="local or remote cover path to include in full preview")
    preview.add_argument("--dry-run", action="store_true", help="validate and print report without writing files")
    preview.set_defaults(func=command_preview)

    wenyan = sub.add_parser("prepare-wenyan", help="generate Wenyan-ready Markdown under workspace publishing/wechat")
    wenyan.add_argument("source", help="workspace platforms/wechat/*.md source file")
    wenyan.add_argument("--cover", help="local or remote cover path to write into Wenyan frontmatter")
    wenyan.add_argument("--dry-run", action="store_true", help="print Wenyan-ready Markdown without writing files")
    wenyan.set_defaults(func=command_prepare_wenyan)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
