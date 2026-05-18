"""Sync Wiki.js TH locale navigation from EN locale.

See docs/superpowers/specs/2026-05-18-th-navigation-design.md for design.
"""
from __future__ import annotations

from enum import Enum
import logging
import re
import uuid
from pathlib import Path
from typing import Any

import frontmatter
import yaml

log = logging.getLogger("sync_nav")


# ===== Section 1: Markdown / YAML parsing =====

_H2_NUMBERED_RE = re.compile(r"^##\s+\d+\.\s+(.+?)\s*$")


def parse_home_headings(home_md: Path) -> list[str]:
    """Parse `## N. <text>` headings from a home.md file, in document order.

    Returns the heading text with the `N. ` numbering prefix stripped.
    Only h2 headings (`## `) that begin with a numbering prefix are
    included; the h1 title and h3+ subheadings are ignored.
    """
    out: list[str] = []
    for line in home_md.read_text(encoding="utf-8").splitlines():
        m = _H2_NUMBERED_RE.match(line)
        if m:
            out.append(m.group(1).strip())
    return out


def build_header_label_map(en_headings: list[str], th_headings: list[str]) -> dict[str, str]:
    """Pair EN and TH home.md headings by index → {en_text: th_text}.

    If the two lists differ in length, pairs up to the shorter list and
    logs a WARNING. Mismatching indices fall back to override / EN label
    in resolve_label().
    """
    if len(en_headings) != len(th_headings):
        log.warning(
            "home.md heading count mismatch: en=%d th=%d — pairing up to min",
            len(en_headings),
            len(th_headings),
        )
    pairs = zip(en_headings, th_headings)
    return {en: th for en, th in pairs}


# ===== Section 2: Overrides loader =====


def load_overrides(path: Path) -> dict[str, dict[str, str]]:
    """Load nav-overrides.yaml; missing sections default to empty dicts."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {
        "headers": dict(raw.get("headers") or {}),
        "links": dict(raw.get("links") or {}),
    }


# ===== Section 3: TH page title resolution =====


def resolve_th_page_title(repo_root: Path, target: str) -> str | None:
    """Look up the `title:` frontmatter from a TH page given a Wiki.js target.

    Tries both '<rel>.md' and '<rel>/index.md' — Wiki.js page targets may
    refer to either a file or a folder. Returns None if no file is found
    or the frontmatter has no `title` key.
    """
    rel = target.lstrip("/")
    for candidate in (
        repo_root / f"{rel}.md",
        repo_root / rel / "index.md",
    ):
        if candidate.exists():
            post = frontmatter.load(str(candidate))
            title = post.metadata.get("title")
            return str(title) if title else None
    return None


# ===== Section 4: Label resolution =====


class LabelSource(str, Enum):
    """Where a TH label was sourced from. Used in --verbose output."""
    FRONTMATTER = "frontmatter"
    HOME_MD = "home.md"
    OVERRIDE = "override"
    FALLBACK = "fallback"
    NONE = "none"  # divider items have no label


def resolve_label(
    item: dict[str, Any],
    *,
    repo_root: Path,
    header_map: dict[str, str],
    overrides: dict[str, dict[str, str]],
) -> tuple[str | None, LabelSource]:
    """Resolve the TH label for a navigation item.

    Returns (label, source). Label is None for dividers. Source records
    which of the three input sources produced the label (or FALLBACK
    when none did, in which case the EN label is returned verbatim).
    """
    kind = item["kind"]
    if kind == "divider":
        return None, LabelSource.NONE

    if kind == "link" and item["targetType"] == "page":
        title = resolve_th_page_title(repo_root, item["target"])
        if title:
            return title, LabelSource.FRONTMATTER
        return item["label"], LabelSource.FALLBACK

    if kind == "header":
        if item["label"] in header_map:
            return header_map[item["label"]], LabelSource.HOME_MD
        if item["label"] in overrides["headers"]:
            return overrides["headers"][item["label"]], LabelSource.OVERRIDE
        return item["label"], LabelSource.FALLBACK

    if kind == "link" and item["targetType"] == "url":
        if item["target"] in overrides["links"]:
            return overrides["links"][item["target"]], LabelSource.OVERRIDE
        return item["label"], LabelSource.FALLBACK

    # Unknown kind/targetType — preserve EN label
    return item["label"], LabelSource.FALLBACK


# ===== Section 5: Item transformation =====


def transform_item(
    en_item: dict[str, Any],
    *,
    repo_root: Path,
    header_map: dict[str, str],
    overrides: dict[str, dict[str, str]],
) -> dict[str, Any]:
    """Clone an EN navigation item into its TH counterpart.

    - id        → fresh UUIDv4
    - target    → /en/... rewritten to /th/... (only for kind=link, targetType=page)
    - label     → resolved via resolve_label() (3 sources)
    - icon, visibilityMode, visibilityGroups, kind, targetType: preserved

    Does not mutate the input item.
    """
    new = dict(en_item)
    new["id"] = str(uuid.uuid4())

    if new["kind"] == "link" and new["targetType"] == "page":
        new["target"] = new["target"].replace("/en/", "/th/", 1)

    label, _source = resolve_label(
        new,
        repo_root=repo_root,
        header_map=header_map,
        overrides=overrides,
    )
    # Dividers return None from resolve_label — keep their label field empty
    new["label"] = label if label is not None else ""

    # Defensive: copy mutable nested fields so caller can't mutate ours
    new["visibilityGroups"] = list(new.get("visibilityGroups") or [])
    return new


# ===== Section 6: List transformation with source counts =====


def transform_items(
    en_items: list[dict[str, Any]],
    *,
    repo_root: Path,
    header_map: dict[str, str],
    overrides: dict[str, dict[str, str]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Transform a list of EN items into TH equivalents, with source counts.

    Returns (new_items, counts) where counts is keyed by LabelSource.value.
    """
    new_items: list[dict[str, Any]] = []
    counts = {s.value: 0 for s in LabelSource}
    for item in en_items:
        # Resolve label twice (once here for counting, once inside
        # transform_item) — second resolution is cheap and keeps
        # transform_item self-contained.
        _label, source = resolve_label(
            item,
            repo_root=repo_root,
            header_map=header_map,
            overrides=overrides,
        )
        # For "link + page", resolve_label sees /en/... — same result as /th/...
        # since both paths lead to the same frontmatter lookup outcome
        # (file existence check tries /th/ via transform_item rewrite).
        # But here we haven't rewritten yet, so we need to test against /th/.
        # Re-resolve with rewritten target for accurate count:
        if item["kind"] == "link" and item["targetType"] == "page":
            rewritten = dict(item)
            rewritten["target"] = item["target"].replace("/en/", "/th/", 1)
            _label, source = resolve_label(
                rewritten,
                repo_root=repo_root,
                header_map=header_map,
                overrides=overrides,
            )
        counts[source.value] += 1
        new_items.append(
            transform_item(
                item,
                repo_root=repo_root,
                header_map=header_map,
                overrides=overrides,
            )
        )
    return new_items, counts


# ===== Section 7: Diff computation =====


def compute_diff(
    th_old: list[dict[str, Any]],
    th_new: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute a high-level diff summary for the TH tree.

    For the report headline only. Per-item diffs are printed inline
    during transform_items via the LabelSource counts and verbose log.
    """
    return {
        "old_count": len(th_old),
        "new_count": len(th_new),
        "all_new": len(th_old) == 0,
    }
