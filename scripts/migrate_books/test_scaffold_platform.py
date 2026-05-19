"""Tests for scaffold_platform.py."""
from pathlib import Path

import frontmatter

from scripts.migrate_books.scaffold_platform import (
    render_page,
    iter_pages,
    PageSpec,
)


SAMPLE_SPEC = PageSpec(
    path="clusters/home.md",
    title_en="Clusters",
    title_th="Clusters",
    description="Cluster mgmt.",
    tags=["book/platform", "clusters"],
    at_a_glance=["What a cluster is"],
    references=["../carmen-platform/SITEMAP.md"],
    todo=["Document permissions"],
)


def test_render_page_has_frontmatter_with_title():
    out = render_page(SAMPLE_SPEC, locale="en", today_iso="2026-05-19T00:00:00.000Z")
    post = frontmatter.loads(out)
    assert post.metadata["title"] == "Clusters"
    assert post.metadata["description"] == "Cluster mgmt."
    assert post.metadata["published"] is True
    assert post.metadata["editor"] == "markdown"
    assert post.metadata["date"] == "2026-05-19T00:00:00.000Z"
    assert post.metadata["dateCreated"] == "2026-05-19T00:00:00.000Z"


def test_render_page_uses_th_title_for_th_locale():
    spec = PageSpec(**{**SAMPLE_SPEC.__dict__, "title_th": "คลัสเตอร์"})
    out = render_page(spec, locale="th", today_iso="2026-05-19T00:00:00.000Z")
    post = frontmatter.loads(out)
    assert post.metadata["title"] == "คลัสเตอร์"


def test_render_page_has_three_numbered_sections():
    out = render_page(SAMPLE_SPEC, locale="en", today_iso="2026-05-19T00:00:00.000Z")
    assert "## 1. At a Glance" in out
    assert "## 2. References" in out
    assert "## 3. TODO" in out


def test_render_page_lists_references_and_todo():
    out = render_page(SAMPLE_SPEC, locale="en", today_iso="2026-05-19T00:00:00.000Z")
    assert "../carmen-platform/SITEMAP.md" in out
    assert "Document permissions" in out


def test_render_page_at_a_glance_bullets_are_emitted():
    out = render_page(SAMPLE_SPEC, locale="en", today_iso="2026-05-19T00:00:00.000Z")
    assert "- What a cluster is" in out


def test_iter_pages_loads_yaml_into_specs(tmp_path: Path):
    cfg = tmp_path / "pages.yaml"
    cfg.write_text(
        """
book: platform
pages:
  - path: a/b.md
    title_en: A
    title_th: A-th
    description: d
    tags: [book/platform]
    at_a_glance: [g]
    references: [r]
    todo: [t]
""".strip(),
        encoding="utf-8",
    )
    specs = list(iter_pages(cfg))
    assert len(specs) == 1
    assert specs[0].path == "a/b.md"
    assert specs[0].title_en == "A"
    assert specs[0].title_th == "A-th"
