# TH Locale Navigation Sync — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `scripts/sync_nav.py` that mirrors the Wiki.js EN navigation tree into the TH locale via GraphQL, with TH labels resolved from `th/*.md` frontmatter, `th/home.md` section headings, and a manual overrides YAML.

**Architecture:** Single Python script (~400 LOC) split into pure functions (parsing, label resolution, transform, diff) and a thin I/O layer (GraphQL fetch/push). Pure functions are unit-tested with pytest; GraphQL plumbing is verified via `--dry-run` against the live Wiki.js dev instance.

**Tech Stack:** Python 3.11+, `gql` (GraphQL client over `requests`), `python-frontmatter`, `pyyaml`, `pytest`. Run locally on developer machine; no CI integration.

**Spec:** [`docs/superpowers/specs/2026-05-18-th-navigation-design.md`](../specs/2026-05-18-th-navigation-design.md)

**Spec deviation note:** The spec named the file `scripts/sync-nav.py` (hyphen). The plan uses `scripts/sync_nav.py` (underscore) so the same module is importable by tests. The CLI invocation in the spec (`python scripts/sync-nav.py …`) becomes `python scripts/sync_nav.py …`. README documents the actual command.

---

## File Structure

```
carmen-wiki/
├── scripts/
│   ├── sync_nav.py             # main module — CLI entry + all logic
│   ├── test_sync_nav.py        # pytest unit tests
│   ├── conftest.py             # shared pytest fixtures (tmp th/ tree, sample tree)
│   ├── nav-overrides.yaml      # manual label overrides (committed, starts empty)
│   ├── requirements.txt        # pinned: gql, pyyaml, python-frontmatter, pytest
│   └── README.md               # usage, env setup, dry-run, troubleshooting
├── .env.example                # WIKI_API_URL, WIKI_API_TOKEN — committed template
├── .gitignore                  # add .env, scripts/.env, .pytest_cache
└── docs/superpowers/specs/2026-05-18-th-navigation-design.md   # already exists
```

**Single-file rationale:** `sync_nav.py` stays one file because its sections (label resolution, transform, GraphQL, diff, CLI) are tightly coupled to the same data shape (NavigationItem dicts). Splitting into a package would force boundary types that don't yet earn their keep. Internal sections are separated by clear `# ===== Section =====` headers.

---

## Task 1: Scaffolding — directories, requirements, env, gitignore

**Files:**
- Create: `scripts/requirements.txt`
- Create: `scripts/__init__.py` (empty — makes `scripts/` a package so tests can `from scripts.sync_nav import …`)
- Create: `.env.example`
- Modify: `.gitignore`
- Create: `scripts/README.md` (skeleton, will be filled in Task 13)

- [ ] **Step 1: Create `scripts/requirements.txt`**

```
gql[requests]==3.5.0
python-frontmatter==1.1.0
pyyaml==6.0.2
pytest==8.3.4
```

- [ ] **Step 2: Create empty `scripts/__init__.py`**

```python
```

(Empty file — its existence is what matters.)

- [ ] **Step 3: Create `.env.example` at repo root**

```
# Wiki.js GraphQL endpoint
WIKI_API_URL=http://dev.blueledgers.com:3987/graphql

# API token from Wiki.js admin → API Access
# Must have navigation read + manage scopes
WIKI_API_TOKEN=
```

- [ ] **Step 4: Update `.gitignore`**

Append at end of `/Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki/.gitignore`:

```
# Sync-nav script — local env and pytest artifacts
.env
scripts/.env
.pytest_cache/
```

- [ ] **Step 5: Create `scripts/README.md` skeleton**

```markdown
# scripts/

Tooling for the carmen-wiki content repo.

## sync_nav.py

Sync the Wiki.js TH locale navigation from the EN locale.

(Full usage docs filled in by Task 13.)
```

- [ ] **Step 6: Install deps and verify pytest runs**

Run:
```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
python3 -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt
pytest scripts/ -v
```

Expected: pytest collects 0 tests, exits 5 ("no tests ran"). Confirms deps install and pytest can find the package.

- [ ] **Step 7: Add `.venv/` to `.gitignore`**

Append:
```
.venv/
```

- [ ] **Step 8: Commit**

```bash
git add scripts/__init__.py scripts/requirements.txt scripts/README.md .env.example .gitignore
git commit -m "$(cat <<'EOF'
scripts: scaffold sync_nav package

Add scripts/ Python package with requirements, env template,
and gitignore entries. Empty skeleton — implementation follows.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: home.md heading parser

**Files:**
- Create: `scripts/sync_nav.py` (start with this function only)
- Create: `scripts/test_sync_nav.py` (start with these tests only)
- Create: `scripts/conftest.py`

- [ ] **Step 1: Add fixture in `scripts/conftest.py`**

```python
"""Shared pytest fixtures for sync_nav tests."""
from pathlib import Path
import pytest


@pytest.fixture
def repo_root() -> Path:
    """Absolute path to the carmen-wiki repo root (parent of scripts/)."""
    return Path(__file__).resolve().parent.parent
```

- [ ] **Step 2: Write failing test in `scripts/test_sync_nav.py`**

```python
"""Unit tests for sync_nav."""
from pathlib import Path

from scripts.sync_nav import parse_home_headings


def test_parse_home_headings_returns_index_keyed_dict(tmp_path: Path):
    """Headings are returned in index order as a list of strings."""
    home = tmp_path / "home.md"
    home.write_text(
        "---\ntitle: Home\n---\n\n"
        "# Title\n\n"
        "## 1. First\n\nbody\n\n"
        "## 2. Second\n\nbody\n\n"
        "## 3. Third\n",
        encoding="utf-8",
    )
    assert parse_home_headings(home) == ["First", "Second", "Third"]


def test_parse_home_headings_strips_leading_number(tmp_path: Path):
    """Numbering prefix `N. ` is stripped from each heading."""
    home = tmp_path / "home.md"
    home.write_text("## 1. Procure-to-Pay\n## 2. Inventory\n", encoding="utf-8")
    assert parse_home_headings(home) == ["Procure-to-Pay", "Inventory"]


def test_parse_home_headings_ignores_h1_and_h3(tmp_path: Path):
    """Only ## (h2) headings count."""
    home = tmp_path / "home.md"
    home.write_text(
        "# Top\n## 1. A\n### 1.1 A-sub\n## 2. B\n",
        encoding="utf-8",
    )
    assert parse_home_headings(home) == ["A", "B"]
```

- [ ] **Step 3: Run test to verify it fails**

Run:
```bash
pytest scripts/test_sync_nav.py -v
```

Expected: 3 failures with `ImportError: cannot import name 'parse_home_headings' from 'scripts.sync_nav'`.

- [ ] **Step 4: Create `scripts/sync_nav.py` with the function**

```python
"""Sync Wiki.js TH locale navigation from EN locale.

See docs/superpowers/specs/2026-05-18-th-navigation-design.md for design.
"""
from __future__ import annotations

import re
from pathlib import Path


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
```

- [ ] **Step 5: Run tests to verify they pass**

Run:
```bash
pytest scripts/test_sync_nav.py -v
```

Expected: 3 passes.

- [ ] **Step 6: Smoke-test against the real home.md files**

Run:
```bash
python3 -c "
from pathlib import Path
from scripts.sync_nav import parse_home_headings
root = Path('.').resolve()
print('EN:', parse_home_headings(root / 'en/home.md'))
print('TH:', parse_home_headings(root / 'th/home.md'))
"
```

Expected: two lists with the same length. EN starts with `['About This Wiki', 'Dashboard', 'Procure-to-Pay', 'Inventory Control', …]`; TH starts with `['เกี่ยวกับวิกินี้', 'แดชบอร์ด', 'Procure-to-Pay', 'การควบคุมคลังสินค้า', …]`.

- [ ] **Step 7: Commit**

```bash
git add scripts/sync_nav.py scripts/test_sync_nav.py scripts/conftest.py
git commit -m "$(cat <<'EOF'
scripts(sync_nav): add home.md heading parser

Parses `## N. <text>` h2 headings from a home.md file in order.
Strips the numbering prefix; ignores h1 and h3+. First pure function
in the sync_nav module — covered by pytest unit tests.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Header-label map (EN → TH by index)

**Files:**
- Modify: `scripts/sync_nav.py` — add `build_header_label_map`
- Modify: `scripts/test_sync_nav.py` — add tests

- [ ] **Step 1: Write failing tests**

Append to `scripts/test_sync_nav.py`:

```python
from scripts.sync_nav import build_header_label_map


def test_build_header_label_map_pairs_by_index():
    en = ["About", "Dashboard", "Procure-to-Pay"]
    th = ["เกี่ยวกับ", "แดชบอร์ด", "Procure-to-Pay"]
    assert build_header_label_map(en, th) == {
        "About": "เกี่ยวกับ",
        "Dashboard": "แดชบอร์ด",
        "Procure-to-Pay": "Procure-to-Pay",
    }


def test_build_header_label_map_mismatch_returns_partial_and_warns(caplog):
    """If lists differ in length, pair up to min(len) and log a warning."""
    en = ["A", "B", "C"]
    th = ["ก", "ข"]
    with caplog.at_level("WARNING"):
        out = build_header_label_map(en, th)
    assert out == {"A": "ก", "B": "ข"}
    assert any("home.md heading count" in r.message for r in caplog.records)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest scripts/test_sync_nav.py -v
```

Expected: 2 new failures with `ImportError: cannot import name 'build_header_label_map'`.

- [ ] **Step 3: Add implementation to `scripts/sync_nav.py`**

Append after `parse_home_headings`:

```python
import logging

log = logging.getLogger("sync_nav")


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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest scripts/test_sync_nav.py -v
```

Expected: 5 passes.

- [ ] **Step 5: Commit**

```bash
git add scripts/sync_nav.py scripts/test_sync_nav.py
git commit -m "$(cat <<'EOF'
scripts(sync_nav): pair EN and TH home.md headings by index

build_header_label_map zips parsed headings into an EN→TH dict.
Length mismatch is non-fatal — pairs up to min and logs a warning.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Overrides YAML loader

**Files:**
- Create: `scripts/nav-overrides.yaml`
- Modify: `scripts/sync_nav.py` — add `load_overrides`
- Modify: `scripts/test_sync_nav.py` — add tests

- [ ] **Step 1: Create `scripts/nav-overrides.yaml`**

```yaml
# Manual TH label overrides for Wiki.js navigation sync.
#
# Used only when the primary sources cannot resolve a label:
#   - headers/: when EN heading text has no match in th/home.md
#   - links/:   for kind=link items with targetType=url (external URLs)
#
# Keys must match EXACTLY (case-sensitive, whitespace-preserved).

headers: {}
  # Example:
  # "Procure-to-Pay": "จัดซื้อจัดจ้าง (Procure-to-Pay)"

links: {}
  # Example:
  # "https://github.com/CarmenSoftware-organization/carmen-wiki": "GitHub repository"
```

- [ ] **Step 2: Write failing tests**

Append to `scripts/test_sync_nav.py`:

```python
from scripts.sync_nav import load_overrides


def test_load_overrides_parses_headers_and_links(tmp_path: Path):
    cfg = tmp_path / "nav-overrides.yaml"
    cfg.write_text(
        'headers:\n'
        '  "Procure-to-Pay": "จัดซื้อ"\n'
        'links:\n'
        '  "https://example.com": "ตัวอย่าง"\n',
        encoding="utf-8",
    )
    out = load_overrides(cfg)
    assert out == {
        "headers": {"Procure-to-Pay": "จัดซื้อ"},
        "links": {"https://example.com": "ตัวอย่าง"},
    }


def test_load_overrides_empty_sections(tmp_path: Path):
    """Empty mappings (`{}`) become empty dicts."""
    cfg = tmp_path / "nav-overrides.yaml"
    cfg.write_text("headers: {}\nlinks: {}\n", encoding="utf-8")
    assert load_overrides(cfg) == {"headers": {}, "links": {}}


def test_load_overrides_missing_section_defaults_to_empty(tmp_path: Path):
    """If `headers:` or `links:` is omitted, default to empty dict."""
    cfg = tmp_path / "nav-overrides.yaml"
    cfg.write_text("headers:\n  A: B\n", encoding="utf-8")
    out = load_overrides(cfg)
    assert out == {"headers": {"A": "B"}, "links": {}}
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
pytest scripts/test_sync_nav.py -v
```

Expected: 3 new failures.

- [ ] **Step 4: Add implementation**

Append to `scripts/sync_nav.py`:

```python
import yaml


def load_overrides(path: Path) -> dict[str, dict[str, str]]:
    """Load nav-overrides.yaml; missing sections default to empty dicts."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {
        "headers": dict(raw.get("headers") or {}),
        "links": dict(raw.get("links") or {}),
    }
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest scripts/test_sync_nav.py -v
```

Expected: 8 passes.

- [ ] **Step 6: Commit**

```bash
git add scripts/sync_nav.py scripts/test_sync_nav.py scripts/nav-overrides.yaml
git commit -m "$(cat <<'EOF'
scripts(sync_nav): YAML overrides loader

Reads scripts/nav-overrides.yaml into a {headers, links} dict.
Missing sections default to empty — committed file starts empty
with example-comment-only entries.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Frontmatter title lookup

**Files:**
- Modify: `scripts/sync_nav.py` — add `resolve_th_page_title`
- Modify: `scripts/test_sync_nav.py` — add tests

- [ ] **Step 1: Write failing tests**

Append to `scripts/test_sync_nav.py`:

```python
from scripts.sync_nav import resolve_th_page_title


def _write_md(path: Path, title: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\ntitle: {title}\ndescription: x\npublished: true\n---\n\n# {title}\n",
        encoding="utf-8",
    )


def test_resolve_th_page_title_file_form(tmp_path: Path):
    """target='/th/foo' resolves to th/foo.md if that file exists."""
    _write_md(tmp_path / "th" / "foo.md", "หน้า Foo")
    assert resolve_th_page_title(tmp_path, "/th/foo") == "หน้า Foo"


def test_resolve_th_page_title_folder_form(tmp_path: Path):
    """target='/th/foo' resolves to th/foo/index.md if no th/foo.md exists."""
    _write_md(tmp_path / "th" / "foo" / "index.md", "Foo Index")
    assert resolve_th_page_title(tmp_path, "/th/foo") == "Foo Index"


def test_resolve_th_page_title_prefers_file_over_folder(tmp_path: Path):
    """If both th/foo.md and th/foo/index.md exist, the file wins."""
    _write_md(tmp_path / "th" / "foo.md", "FILE")
    _write_md(tmp_path / "th" / "foo" / "index.md", "FOLDER")
    assert resolve_th_page_title(tmp_path, "/th/foo") == "FILE"


def test_resolve_th_page_title_missing_returns_none(tmp_path: Path):
    """No file exists → None (caller falls back to EN label)."""
    assert resolve_th_page_title(tmp_path, "/th/missing") is None


def test_resolve_th_page_title_handles_subpath(tmp_path: Path):
    """target='/th/foo/bar' resolves to th/foo/bar.md."""
    _write_md(tmp_path / "th" / "foo" / "bar.md", "Bar")
    assert resolve_th_page_title(tmp_path, "/th/foo/bar") == "Bar"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest scripts/test_sync_nav.py -v
```

Expected: 5 new failures.

- [ ] **Step 3: Add implementation**

Append to `scripts/sync_nav.py`:

```python
import frontmatter


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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest scripts/test_sync_nav.py -v
```

Expected: 13 passes.

- [ ] **Step 5: Commit**

```bash
git add scripts/sync_nav.py scripts/test_sync_nav.py
git commit -m "$(cat <<'EOF'
scripts(sync_nav): resolve TH page titles from frontmatter

resolve_th_page_title takes a Wiki.js target like /th/foo and reads
the `title:` field from either th/foo.md or th/foo/index.md.
Returns None when no file is found.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: `resolve_label` — combine 3 sources

**Files:**
- Modify: `scripts/sync_nav.py` — add `resolve_label` and `LabelSource` enum
- Modify: `scripts/test_sync_nav.py` — add tests

- [ ] **Step 1: Write failing tests**

Append to `scripts/test_sync_nav.py`:

```python
from scripts.sync_nav import resolve_label, LabelSource


def _item(**kw):
    """Build a minimal navigation item dict with sensible defaults."""
    base = {
        "id": "abc",
        "kind": "link",
        "label": "EN Label",
        "icon": "",
        "targetType": "page",
        "target": "/th/foo",
        "visibilityMode": "all",
        "visibilityGroups": [],
    }
    base.update(kw)
    return base


def test_resolve_label_link_page_uses_frontmatter(tmp_path: Path):
    _write_md(tmp_path / "th" / "foo.md", "หน้า Foo")
    label, source = resolve_label(
        _item(),
        repo_root=tmp_path,
        header_map={},
        overrides={"headers": {}, "links": {}},
    )
    assert label == "หน้า Foo"
    assert source == LabelSource.FRONTMATTER


def test_resolve_label_link_page_missing_falls_back_to_en(tmp_path: Path):
    label, source = resolve_label(
        _item(target="/th/missing", label="Missing"),
        repo_root=tmp_path,
        header_map={},
        overrides={"headers": {}, "links": {}},
    )
    assert label == "Missing"
    assert source == LabelSource.FALLBACK


def test_resolve_label_header_uses_home_md(tmp_path: Path):
    label, source = resolve_label(
        _item(kind="header", label="Procure-to-Pay", target=""),
        repo_root=tmp_path,
        header_map={"Procure-to-Pay": "จัดซื้อจัดจ้าง"},
        overrides={"headers": {}, "links": {}},
    )
    assert label == "จัดซื้อจัดจ้าง"
    assert source == LabelSource.HOME_MD


def test_resolve_label_header_falls_back_to_override(tmp_path: Path):
    """home.md doesn't have it → overrides.headers wins."""
    label, source = resolve_label(
        _item(kind="header", label="X", target=""),
        repo_root=tmp_path,
        header_map={},
        overrides={"headers": {"X": "เอกซ์"}, "links": {}},
    )
    assert label == "เอกซ์"
    assert source == LabelSource.OVERRIDE


def test_resolve_label_header_falls_back_to_en(tmp_path: Path):
    """No home.md match, no override → EN label."""
    label, source = resolve_label(
        _item(kind="header", label="Unknown", target=""),
        repo_root=tmp_path,
        header_map={},
        overrides={"headers": {}, "links": {}},
    )
    assert label == "Unknown"
    assert source == LabelSource.FALLBACK


def test_resolve_label_link_url_uses_overrides(tmp_path: Path):
    label, source = resolve_label(
        _item(targetType="url", target="https://example.com", label="Example"),
        repo_root=tmp_path,
        header_map={},
        overrides={"headers": {}, "links": {"https://example.com": "ตัวอย่าง"}},
    )
    assert label == "ตัวอย่าง"
    assert source == LabelSource.OVERRIDE


def test_resolve_label_divider_returns_none(tmp_path: Path):
    label, source = resolve_label(
        _item(kind="divider", label="", target=""),
        repo_root=tmp_path,
        header_map={},
        overrides={"headers": {}, "links": {}},
    )
    assert label is None
    assert source == LabelSource.NONE
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest scripts/test_sync_nav.py -v
```

Expected: 7 new failures.

- [ ] **Step 3: Add implementation**

Append to `scripts/sync_nav.py`:

```python
from enum import Enum
from typing import Any


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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest scripts/test_sync_nav.py -v
```

Expected: 20 passes.

- [ ] **Step 5: Commit**

```bash
git add scripts/sync_nav.py scripts/test_sync_nav.py
git commit -m "$(cat <<'EOF'
scripts(sync_nav): combine 3 label sources in resolve_label

resolve_label takes a nav item plus header_map + overrides + repo_root
and returns (label, source). Source is enumerated (frontmatter,
home.md, override, fallback, none) for verbose reporting.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Transform single item (clone, new id, rewrite path, set label)

**Files:**
- Modify: `scripts/sync_nav.py` — add `transform_item`
- Modify: `scripts/test_sync_nav.py` — add tests

- [ ] **Step 1: Write failing tests**

Append to `scripts/test_sync_nav.py`:

```python
import uuid as _uuid
from scripts.sync_nav import transform_item


def test_transform_item_link_page_rewrites_target(tmp_path: Path):
    _write_md(tmp_path / "th" / "foo.md", "Foo TH")
    en_item = _item(target="/en/foo", label="Foo")
    new = transform_item(
        en_item,
        repo_root=tmp_path,
        header_map={},
        overrides={"headers": {}, "links": {}},
    )
    assert new["target"] == "/th/foo"
    assert new["label"] == "Foo TH"
    assert new["id"] != en_item["id"]  # fresh UUID
    _uuid.UUID(new["id"], version=4)    # parses as UUIDv4


def test_transform_item_link_url_keeps_target(tmp_path: Path):
    en_item = _item(targetType="url", target="https://example.com", label="Ex")
    new = transform_item(
        en_item,
        repo_root=tmp_path,
        header_map={},
        overrides={"headers": {}, "links": {"https://example.com": "ตัวอย่าง"}},
    )
    assert new["target"] == "https://example.com"
    assert new["label"] == "ตัวอย่าง"


def test_transform_item_header_preserves_target(tmp_path: Path):
    en_item = _item(kind="header", label="Procure-to-Pay", target="")
    new = transform_item(
        en_item,
        repo_root=tmp_path,
        header_map={"Procure-to-Pay": "จัดซื้อ"},
        overrides={"headers": {}, "links": {}},
    )
    assert new["target"] == ""
    assert new["label"] == "จัดซื้อ"
    assert new["kind"] == "header"


def test_transform_item_preserves_icon_and_visibility(tmp_path: Path):
    en_item = _item(
        target="/en/foo",
        icon="mdi-folder",
        visibilityMode="restricted",
        visibilityGroups=[1, 2],
    )
    new = transform_item(
        en_item,
        repo_root=tmp_path,
        header_map={},
        overrides={"headers": {}, "links": {}},
    )
    assert new["icon"] == "mdi-folder"
    assert new["visibilityMode"] == "restricted"
    assert new["visibilityGroups"] == [1, 2]


def test_transform_item_does_not_mutate_input(tmp_path: Path):
    en_item = _item(target="/en/foo", label="Foo")
    original = dict(en_item)
    transform_item(
        en_item,
        repo_root=tmp_path,
        header_map={},
        overrides={"headers": {}, "links": {}},
    )
    assert en_item == original
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest scripts/test_sync_nav.py -v
```

Expected: 5 new failures.

- [ ] **Step 3: Add implementation**

Append to `scripts/sync_nav.py`:

```python
import uuid


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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest scripts/test_sync_nav.py -v
```

Expected: 25 passes.

- [ ] **Step 5: Commit**

```bash
git add scripts/sync_nav.py scripts/test_sync_nav.py
git commit -m "$(cat <<'EOF'
scripts(sync_nav): transform single EN item into TH equivalent

transform_item clones an EN nav item, assigns a fresh UUIDv4,
rewrites /en/ → /th/ for page links, and resolves the TH label.
Icon and visibility fields preserved. Input is not mutated.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: Transform full item list + summary counts

**Files:**
- Modify: `scripts/sync_nav.py` — add `transform_items` returning items + counts
- Modify: `scripts/test_sync_nav.py` — add tests

- [ ] **Step 1: Write failing tests**

Append to `scripts/test_sync_nav.py`:

```python
from scripts.sync_nav import transform_items


def test_transform_items_counts_sources(tmp_path: Path):
    _write_md(tmp_path / "th" / "a.md", "หน้า A")
    en_items = [
        _item(kind="header", label="Procure-to-Pay", target=""),       # home.md
        _item(target="/en/a", label="A"),                              # frontmatter
        _item(target="/en/missing", label="Missing"),                  # fallback
        _item(targetType="url", target="https://x", label="X"),        # override
        _item(kind="divider", label="", target=""),                    # none
    ]
    new_items, counts = transform_items(
        en_items,
        repo_root=tmp_path,
        header_map={"Procure-to-Pay": "จัดซื้อ"},
        overrides={"headers": {}, "links": {"https://x": "เอ็กซ์"}},
    )
    assert len(new_items) == 5
    assert counts == {
        "frontmatter": 1,
        "home.md": 1,
        "override": 1,
        "fallback": 1,
        "none": 1,
    }
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest scripts/test_sync_nav.py -v
```

Expected: 1 new failure.

- [ ] **Step 3: Add implementation**

Append to `scripts/sync_nav.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest scripts/test_sync_nav.py -v
```

Expected: 26 passes.

- [ ] **Step 5: Commit**

```bash
git add scripts/sync_nav.py scripts/test_sync_nav.py
git commit -m "$(cat <<'EOF'
scripts(sync_nav): transform list with per-source counts

transform_items wraps transform_item over a list and returns counts
per LabelSource (frontmatter/home.md/override/fallback/none) for the
summary report.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: Diff computation + report formatting

**Files:**
- Modify: `scripts/sync_nav.py` — add `compute_diff` and `format_diff_line`
- Modify: `scripts/test_sync_nav.py` — add tests

- [ ] **Step 1: Write failing tests**

Append to `scripts/test_sync_nav.py`:

```python
from scripts.sync_nav import compute_diff


def test_compute_diff_empty_to_new():
    """First sync — th_old is empty."""
    th_old = []
    th_new = [_item(target="/th/foo", label="Foo")]
    diff = compute_diff(th_old, th_new)
    assert diff == {"old_count": 0, "new_count": 1, "all_new": True}


def test_compute_diff_replacement():
    """Re-sync — th_old has items, replaced."""
    th_old = [_item(target="/th/foo", label="OLD")]
    th_new = [_item(target="/th/foo", label="NEW")]
    diff = compute_diff(th_old, th_new)
    assert diff == {"old_count": 1, "new_count": 1, "all_new": False}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest scripts/test_sync_nav.py -v
```

Expected: 2 new failures.

- [ ] **Step 3: Add implementation**

Append to `scripts/sync_nav.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest scripts/test_sync_nav.py -v
```

Expected: 28 passes.

- [ ] **Step 5: Commit**

```bash
git add scripts/sync_nav.py scripts/test_sync_nav.py
git commit -m "$(cat <<'EOF'
scripts(sync_nav): compute diff summary for TH tree

compute_diff returns a small summary (old_count, new_count, all_new)
used in the report headline. Per-item changes are reported inline
during transform_items via LabelSource counts.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 10: GraphQL fetch + push (live I/O — no mock tests)

**Files:**
- Modify: `scripts/sync_nav.py` — add `fetch_navigation`, `push_navigation`, `assert_static_mode`

Plumbing functions touching the live Wiki.js API. Verified end-to-end via `--dry-run` in Task 13, not unit tests — mocking `gql` thoroughly would only test the mock.

- [ ] **Step 1: Add GraphQL queries as module-level constants**

Append to `scripts/sync_nav.py`:

```python
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport


_QUERY_NAVIGATION = gql("""
query {
  navigation {
    tree {
      locale
      items {
        id
        kind
        label
        icon
        targetType
        target
        visibilityMode
        visibilityGroups
      }
    }
    config { mode }
  }
}
""")

_MUTATION_UPDATE_TREE = gql("""
mutation($tree: [NavigationTreeInput]!) {
  navigation {
    updateTree(tree: $tree) {
      responseResult { succeeded errorCode message }
    }
  }
}
""")
```

- [ ] **Step 2: Add the client factory**

```python
def _make_client(api_url: str, api_token: str) -> Client:
    transport = RequestsHTTPTransport(
        url=api_url,
        headers={"Authorization": f"Bearer {api_token}"},
        retries=2,
        timeout=30,
    )
    return Client(transport=transport, fetch_schema_from_transport=False)
```

- [ ] **Step 3: Add `fetch_navigation`**

```python
def fetch_navigation(api_url: str, api_token: str) -> dict[str, Any]:
    """Fetch the full navigation tree + config mode.

    Returns the raw `navigation` payload: {tree: [...], config: {mode: ...}}.
    """
    client = _make_client(api_url, api_token)
    result = client.execute(_QUERY_NAVIGATION)
    return result["navigation"]
```

- [ ] **Step 4: Add `assert_static_mode`**

```python
def assert_static_mode(nav_payload: dict[str, Any]) -> None:
    """Abort unless Wiki.js navigation mode is STATIC.

    Other modes (NONE, TREE, MIXED) either provide no static tree to
    sync or would be partially overwritten in ways the script doesn't
    handle.
    """
    mode = nav_payload.get("config", {}).get("mode")
    if mode != "STATIC":
        raise SystemExit(
            f"Wiki.js navigation mode is {mode!r}, not STATIC. "
            "Set Navigation Mode to Static in Wiki.js admin "
            "(Administration → Navigation → Mode) before running this script."
        )
```

- [ ] **Step 5: Add `push_navigation`**

```python
def push_navigation(
    api_url: str,
    api_token: str,
    tree: list[dict[str, Any]],
) -> None:
    """Push the full navigation tree via updateTree mutation.

    `tree` is a list of {locale, items} dicts covering ALL locales
    Wiki.js currently knows about — partial pushes wipe missing locales.
    Raises SystemExit if the mutation reports failure.
    """
    client = _make_client(api_url, api_token)
    result = client.execute(_MUTATION_UPDATE_TREE, variable_values={"tree": tree})
    rr = result["navigation"]["updateTree"]["responseResult"]
    if not rr["succeeded"]:
        raise SystemExit(
            f"updateTree failed: code={rr['errorCode']} message={rr['message']}"
        )
```

- [ ] **Step 6: Re-run all tests (sanity check no regressions)**

```bash
pytest scripts/test_sync_nav.py -v
```

Expected: 28 passes (no new tests in this task — verification is end-to-end in Task 13).

- [ ] **Step 7: Commit**

```bash
git add scripts/sync_nav.py
git commit -m "$(cat <<'EOF'
scripts(sync_nav): GraphQL fetch/push and mode assertion

Adds the live I/O layer: fetch_navigation reads the full tree,
push_navigation writes it back, assert_static_mode aborts when
Wiki.js mode is not STATIC. Verified end-to-end via --dry-run
in CLI task, not unit-tested.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 11: Report formatting (verbose item lines + summary)

**Files:**
- Modify: `scripts/sync_nav.py` — add `format_item_line` and `format_summary`
- Modify: `scripts/test_sync_nav.py` — add tests

- [ ] **Step 1: Write failing tests**

Append to `scripts/test_sync_nav.py`:

```python
from scripts.sync_nav import format_item_line, format_summary


def test_format_item_line_link_page():
    en = _item(target="/en/purchase-request", label="Purchase Request")
    th = _item(target="/th/purchase-request", label="คำขอซื้อ")
    line = format_item_line(en, th, LabelSource.FRONTMATTER)
    assert "/en/purchase-request" in line
    assert "/th/purchase-request" in line
    assert "คำขอซื้อ" in line
    assert "[frontmatter]" in line
    assert line.startswith("  ✓")


def test_format_item_line_fallback_has_warning_marker():
    en = _item(target="/en/missing", label="Missing")
    th = _item(target="/th/missing", label="Missing")
    line = format_item_line(en, th, LabelSource.FALLBACK)
    assert line.startswith("  ⚠")
    assert "[fallback]" in line


def test_format_summary_one_line():
    counts = {
        "frontmatter": 29,
        "home.md": 6,
        "override": 4,
        "fallback": 3,
        "none": 0,
    }
    s = format_summary(42, counts)
    assert "42 items" in s
    assert "29 frontmatter" in s
    assert "6 home.md" in s
    assert "4 override" in s
    assert "3 fallback" in s
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest scripts/test_sync_nav.py -v
```

Expected: 3 new failures.

- [ ] **Step 3: Add implementation**

Append to `scripts/sync_nav.py`:

```python
def format_item_line(
    en_item: dict[str, Any],
    th_item: dict[str, Any],
    source: LabelSource,
) -> str:
    """Single-line verbose report entry for one transformed nav item."""
    marker = "⚠" if source == LabelSource.FALLBACK else "✓"
    kind = en_item["kind"]
    if kind == "header":
        return (
            f"  {marker} header  {en_item['label']!r:30s} →  "
            f"{th_item['label']!r}   [{source.value}]"
        )
    if kind == "divider":
        return f"  {marker} divider"
    # link
    return (
        f"  {marker} link    {en_item['target']:30s} →  "
        f"{th_item['target']:30s} {th_item['label']!r}  [{source.value}]"
    )


def format_summary(total: int, counts: dict[str, int]) -> str:
    """Single-line summary across all items."""
    return (
        f"Summary: {total} items  "
        f"·  {counts.get('frontmatter', 0)} frontmatter  "
        f"·  {counts.get('home.md', 0)} home.md  "
        f"·  {counts.get('override', 0)} override  "
        f"·  {counts.get('fallback', 0)} fallback"
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest scripts/test_sync_nav.py -v
```

Expected: 31 passes.

- [ ] **Step 5: Commit**

```bash
git add scripts/sync_nav.py scripts/test_sync_nav.py
git commit -m "$(cat <<'EOF'
scripts(sync_nav): report line + summary formatters

format_item_line renders one verbose-mode line per nav item with a
marker (✓/⚠) and the label source. format_summary renders the one-line
totals at end of run.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 12: CLI entry + orchestration (`main`, argparse, env loading)

**Files:**
- Modify: `scripts/sync_nav.py` — add `main` and `__main__` block
- Modify: `scripts/test_sync_nav.py` — add integration test for the orchestration of pure stages

- [ ] **Step 1: Write a failing integration test**

The test exercises the pure pipeline end-to-end without touching Wiki.js: it injects pre-built EN items, runs `run_sync(...)`, and asserts the returned TH items and counts.

Append to `scripts/test_sync_nav.py`:

```python
from scripts.sync_nav import run_sync


def test_run_sync_full_pipeline(tmp_path: Path):
    """Pure orchestration: given EN items + repo root, produce TH items + counts."""
    # repo layout
    (tmp_path / "th").mkdir()
    _write_md(tmp_path / "th" / "home.md",
              "# H\n## 1. Procure-to-Pay\n")
    (tmp_path / "en").mkdir()
    _write_md(tmp_path / "en" / "home.md",
              "# H\n## 1. Procure-to-Pay\n")
    _write_md(tmp_path / "th" / "pr.md", "คำขอซื้อ")
    overrides_path = tmp_path / "nav-overrides.yaml"
    overrides_path.write_text("headers: {}\nlinks: {}\n", encoding="utf-8")

    en_items = [
        _item(kind="header", label="Procure-to-Pay", target=""),
        _item(target="/en/pr", label="PR"),
    ]

    th_items, counts = run_sync(
        en_items=en_items,
        repo_root=tmp_path,
        overrides_path=overrides_path,
    )
    assert th_items[0]["label"] == "Procure-to-Pay"  # home.md exact-match self-pair
    assert th_items[1]["target"] == "/th/pr"
    assert th_items[1]["label"] == "คำขอซื้อ"
    assert counts["frontmatter"] == 1
    assert counts["home.md"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest scripts/test_sync_nav.py -v
```

Expected: 1 new failure (`ImportError: cannot import name 'run_sync'`).

- [ ] **Step 3: Add `run_sync` (pure orchestration, no I/O)**

Append to `scripts/sync_nav.py`:

```python
def run_sync(
    *,
    en_items: list[dict[str, Any]],
    repo_root: Path,
    overrides_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Pure pipeline: EN items → TH items + counts.

    No GraphQL I/O; called by main() after fetch_navigation and before
    push_navigation. Tested directly in unit tests.
    """
    en_home = parse_home_headings(repo_root / "en" / "home.md")
    th_home = parse_home_headings(repo_root / "th" / "home.md")
    header_map = build_header_label_map(en_home, th_home)
    overrides = load_overrides(overrides_path)
    return transform_items(
        en_items,
        repo_root=repo_root,
        header_map=header_map,
        overrides=overrides,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest scripts/test_sync_nav.py -v
```

Expected: 32 passes.

- [ ] **Step 5: Add CLI `main` + `__main__` block**

Append to `scripts/sync_nav.py`:

```python
# ===== Section 2: CLI =====

import argparse
import os
import sys


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(message)s",
        stream=sys.stderr,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Sync Wiki.js TH navigation from EN.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch + transform + print diff; do not push.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-item label resolution lines.",
    )
    args = parser.parse_args(argv)

    _setup_logging(args.verbose)

    api_url = os.environ.get("WIKI_API_URL")
    api_token = os.environ.get("WIKI_API_TOKEN")
    if not api_url or not api_token:
        print(
            "ERROR: WIKI_API_URL and WIKI_API_TOKEN must be set "
            "(see .env.example). Source your .env first.",
            file=sys.stderr,
        )
        return 2

    repo_root = Path(__file__).resolve().parent.parent
    overrides_path = Path(__file__).resolve().parent / "nav-overrides.yaml"

    # 1. fetch
    print(f"[FETCH]  api={api_url}", file=sys.stderr)
    nav = fetch_navigation(api_url, api_token)
    assert_static_mode(nav)
    tree = nav["tree"]
    en = next((t for t in tree if t["locale"] == "en"), None)
    if en is None:
        print("ERROR: no en locale in Wiki.js navigation tree.", file=sys.stderr)
        return 3
    th_old = next((t for t in tree if t["locale"] == "th"), {"locale": "th", "items": []})
    print(
        f"         mode=STATIC  locales: en ({len(en['items'])} items), "
        f"th ({len(th_old['items'])} items)",
        file=sys.stderr,
    )

    # 2. transform
    print("[XFORM]  resolving labels...", file=sys.stderr)
    th_new_items, counts = run_sync(
        en_items=en["items"],
        repo_root=repo_root,
        overrides_path=overrides_path,
    )

    if args.verbose:
        for en_item, th_item in zip(en["items"], th_new_items):
            _label, source = resolve_label(
                # Use rewritten /th/ target so per-item source matches counts
                {**en_item, "target": en_item["target"].replace("/en/", "/th/", 1)}
                if en_item["kind"] == "link" and en_item["targetType"] == "page"
                else en_item,
                repo_root=repo_root,
                header_map=build_header_label_map(
                    parse_home_headings(repo_root / "en" / "home.md"),
                    parse_home_headings(repo_root / "th" / "home.md"),
                ),
                overrides=load_overrides(overrides_path),
            )
            print(format_item_line(en_item, th_item, source), file=sys.stderr)

    # 3. diff
    diff = compute_diff(th_old["items"], th_new_items)
    print(
        f"[DIFF]   th tree:  {diff['old_count']} → {diff['new_count']} items"
        + ("  (all new)" if diff["all_new"] else ""),
        file=sys.stderr,
    )

    if args.dry_run:
        print("[DRY-RUN] no mutation sent.", file=sys.stderr)
        print(format_summary(len(th_new_items), counts), file=sys.stderr)
        return 0

    # 4. push (full tree, EN unchanged + new TH; preserve any other locales verbatim)
    new_tree = []
    for t in tree:
        if t["locale"] == "th":
            new_tree.append({"locale": "th", "items": th_new_items})
        else:
            new_tree.append(t)
    if not any(t["locale"] == "th" for t in tree):
        new_tree.append({"locale": "th", "items": th_new_items})

    push_navigation(api_url, api_token, new_tree)
    print("[PUSH]   updateTree succeeded.", file=sys.stderr)
    print(format_summary(len(th_new_items), counts), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 6: Run all tests to confirm no regression**

```bash
pytest scripts/test_sync_nav.py -v
```

Expected: 32 passes.

- [ ] **Step 7: Smoke-test CLI argument parsing without env vars**

```bash
unset WIKI_API_URL WIKI_API_TOKEN
python3 scripts/sync_nav.py --dry-run
```

Expected: exit code 2 with error "WIKI_API_URL and WIKI_API_TOKEN must be set".

- [ ] **Step 8: Commit**

```bash
git add scripts/sync_nav.py scripts/test_sync_nav.py
git commit -m "$(cat <<'EOF'
scripts(sync_nav): CLI entry, env loading, orchestration

main() parses --dry-run/--verbose, loads WIKI_API_URL/WIKI_API_TOKEN,
calls fetch → run_sync → diff → optional push. run_sync is the pure
orchestration unit-tested without I/O. Missing env vars abort with
exit 2; missing en locale aborts with exit 3.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 13: Finalize `scripts/README.md`

**Files:**
- Modify: `scripts/README.md` — replace skeleton with complete usage docs

- [ ] **Step 1: Replace `scripts/README.md` with full docs**

```markdown
# scripts/

Tooling for the carmen-wiki content repo.

## sync_nav.py

Mirrors the Wiki.js EN navigation tree into the TH locale.

Design: [`docs/superpowers/specs/2026-05-18-th-navigation-design.md`](../docs/superpowers/specs/2026-05-18-th-navigation-design.md).

### Prerequisites

- Python 3.11+
- A Wiki.js admin API token with navigation read + manage scopes
  (Wiki.js admin → API Access → New API Key)
- Wiki.js navigation mode set to **Static** (admin → Navigation → Mode)

### One-time setup

```bash
cd /path/to/carmen-wiki
python3 -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt

cp .env.example .env
# Edit .env and paste your WIKI_API_TOKEN
```

### Usage

Dry-run (recommended first):

```bash
source .venv/bin/activate
set -a; source .env; set +a
python3 scripts/sync_nav.py --dry-run --verbose
```

Read the per-item lines and the summary. Any `⚠ … [fallback]` line means
the TH label could not be resolved from frontmatter, home.md, or
overrides — fix the cause (write the TH page, add a heading to
`th/home.md`, or add an entry to `nav-overrides.yaml`) before pushing.

Live push:

```bash
python3 scripts/sync_nav.py
```

### Label resolution

For each EN nav item, the TH label is resolved in this order:

1. **Frontmatter** (`link` + `targetType: page`):
   read `title:` from `th/<target>.md` or `th/<target>/index.md`.
2. **home.md** (`header`):
   pair `## N. …` headings between `en/home.md` and `th/home.md` by index.
3. **Override** (`nav-overrides.yaml`):
   manual map for headers and external URLs.
4. **Fallback:** EN label as-is (logged with ⚠ marker).

### Troubleshooting

| Symptom | Likely cause | Fix |
|--------|------|-----|
| `Wiki.js navigation mode is 'TREE', not STATIC.` | Wiki.js mode is auto-tree | Admin → Navigation → Mode: Static |
| Exit 2: `WIKI_API_URL and WIKI_API_TOKEN must be set` | `.env` not sourced or empty | `set -a; source .env; set +a` and verify token |
| `updateTree failed: code=Unauthorized` | Token lacks scopes or expired | Generate a new token with navigation: manage |
| Many `⚠ [fallback]` lines | TH translations missing / home.md headings drifted | Translate the TH pages or sync home.md; add entries to `nav-overrides.yaml` if needed |

### Files

| File | Purpose |
|------|---------|
| `sync_nav.py` | Main module + CLI entry |
| `test_sync_nav.py` | Pytest unit tests for pure functions |
| `conftest.py` | Shared pytest fixtures |
| `nav-overrides.yaml` | Manual label overrides (committed) |
| `requirements.txt` | Pinned Python dependencies |
```

- [ ] **Step 2: Commit**

```bash
git add scripts/README.md
git commit -m "$(cat <<'EOF'
scripts(sync_nav): finalize README with usage and troubleshooting

Replaces the skeleton with prerequisites, setup, dry-run / live-push
commands, label resolution order, and a troubleshooting table.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 14: End-to-end manual verification against dev Wiki.js

This is a manual checklist run by the engineer. No code changes; the outcome is a captured screenshot and a confirmation that TH nav renders correctly.

- [ ] **Step 1: Confirm Wiki.js navigation mode is STATIC**

In a browser, visit `http://dev.blueledgers.com:3987/`, log in as admin, navigate to **Administration → Navigation → Mode**. Confirm it is set to **Static**. If not, switch it (this will surface an empty TH tree which the script then populates).

- [ ] **Step 2: Generate an API token**

In Wiki.js admin → **API Access** → **New API Key**. Scopes: `read:navigation` and `manage:navigation`. Copy the token, paste into `.env` as `WIKI_API_TOKEN`.

- [ ] **Step 3: Run dry-run and review output**

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
source .venv/bin/activate
set -a; source .env; set +a
python3 scripts/sync_nav.py --dry-run --verbose 2>&1 | tee /tmp/sync-nav-dryrun.log
```

Expected: `[DRY-RUN] no mutation sent.` near the end. Review every `⚠ [fallback]` line. For each one, either:
- Create the missing TH page,
- Sync the `th/home.md` heading at that index with `en/home.md`,
- Or add an entry to `scripts/nav-overrides.yaml`.

Re-run dry-run until the only `⚠` lines (if any) are ones you have consciously accepted.

- [ ] **Step 4: Live push**

```bash
python3 scripts/sync_nav.py 2>&1 | tee /tmp/sync-nav-push.log
```

Expected: ends with `[PUSH]   updateTree succeeded.` and the summary line.

- [ ] **Step 5: Browser verification**

Open `http://dev.blueledgers.com:3987/th/home` in a browser (fresh tab, no cache).

Verify:
1. Left sidebar now appears with the same group structure as `/en/home`
2. Top-level group headers expand / collapse on click
3. At least 3 representative module links resolve to existing TH pages:
   - `/th/purchase-request`
   - `/th/good-receive-note`
   - `/th/inventory`
4. Switch the EN/TH language toggle from a deep page (e.g. `/th/costing/calculation-methods`) — the sidebar should swap locale without breaking
5. Open `/en/home` and confirm the EN sidebar is **byte-identical** to before (same items, same labels, same order — same UUIDs since EN was sent back unchanged)

- [ ] **Step 6: Capture a verification screenshot**

Save a screenshot of `/th/home` with the new sidebar visible to `screenshots/th-nav-after-sync.png` (consistent with the repo's screenshot pattern under `/screenshots/...`).

- [ ] **Step 7: Commit any `nav-overrides.yaml` entries added during verification**

```bash
git add scripts/nav-overrides.yaml
git commit -m "$(cat <<'EOF'
scripts(sync_nav): seed nav-overrides.yaml after first sync

Entries added during initial dry-run pass to translate headers /
external links that could not resolve from frontmatter or home.md.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

If no entries were added, skip this commit.

---

## Self-Review Findings

After writing the plan, I reviewed it against the spec.

**Spec coverage:**
- Section 1 Problem — context only, no task needed.
- Section 2 Goal — covered by Tasks 1–14 collectively.
- Section 3 Architecture — Tasks 2–9 (transform pipeline), Task 10 (GraphQL), Task 12 (orchestration).
- Section 4 GraphQL — Task 10.
- Section 5 Sync algorithm — Tasks 2–8 (steps 1–3), Task 9 (step 4 diff), Task 12 (step 5 dry-run gate, step 6 push), Task 11 (step 7 report).
- Section 5.1 `resolve_label` — Task 6 (with path-tries-both-shapes in Task 5).
- Section 5.2 home.md heading parser — Task 2.
- Section 6 File layout — Task 1 (scaffolding) plus the running file structure.
- Section 6.1 `nav-overrides.yaml` — Task 4.
- Section 6.2 `.env.example` — Task 1.
- Section 7 CLI surface — Task 12.
- Section 8 Idempotency — guaranteed by UUID generation in Task 7 and pure functions in Tasks 2–9.
- Section 9 Edge cases — TH page missing (Task 5), mode != STATIC (Task 10), header text changes (overrides in Task 4), URL links (Task 6), dividers (Task 6, 7), visibility/icon (Task 7).
- Section 11 Implementation notes — Python version (Task 1), no content writes (transform_item does not mutate), nav-overrides starts empty (Task 4), README (Task 13).
- Section 12 Verification — Task 14.

**Placeholder scan:** No TBD/TODO. All steps contain runnable commands or actual code. The two `pass` placeholders are not present; the only conscious deferral is Task 10 (no unit tests for live-API code — explicitly documented as "verified end-to-end via --dry-run").

**Type consistency:** `parse_home_headings → list[str]`, `build_header_label_map(list, list) → dict[str, str]`, `load_overrides → dict[str, dict[str, str]]`, `resolve_th_page_title → str | None`, `resolve_label → tuple[str | None, LabelSource]`, `transform_item → dict`, `transform_items → tuple[list[dict], dict[str, int]]`, `compute_diff → dict`, `format_item_line → str`, `format_summary → str`, `run_sync → tuple[list[dict], dict[str, int]]`, `fetch_navigation → dict`, `push_navigation → None`. Signatures match between definition (in implementation step) and usage (in CLI / orchestration). The `LabelSource` enum values (`frontmatter`, `home.md`, `override`, `fallback`, `none`) are consistent across `resolve_label`, `transform_items`, `format_summary`, and `format_item_line`.

Plan is internally consistent. Ready to execute.
