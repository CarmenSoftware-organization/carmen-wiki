"""Sync Wiki.js TH locale navigation from EN locale.

See docs/superpowers/specs/2026-05-18-th-navigation-design.md for design.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

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
