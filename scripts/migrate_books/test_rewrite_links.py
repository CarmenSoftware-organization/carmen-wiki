"""Tests for rewrite_links.py."""
from scripts.migrate_books.rewrite_links import (
    rewrite_text,
    build_mapping,
)


MAPPING = build_mapping(
    modules=["costing", "good-receive-note"],
    book="inventory",
)


def test_rewrites_root_relative_en_page_link():
    src = "See [Costing](/en/costing/calculation-methods)."
    out = rewrite_text(src, MAPPING)
    assert out == "See [Costing](/en/inventory/costing/calculation-methods)."


def test_rewrites_root_relative_th_page_link():
    src = "ดู [Costing](/th/costing/calculation-methods)"
    out = rewrite_text(src, MAPPING)
    assert out == "ดู [Costing](/th/inventory/costing/calculation-methods)"


def test_rewrites_image_reference():
    src = "![receiver](/assets/screenshots/good-receive-note/receiver.png)"
    out = rewrite_text(src, MAPPING)
    assert out == "![receiver](/assets/screenshots/inventory/good-receive-note/receiver.png)"


def test_preserves_anchor():
    src = "[FIFO](/en/costing/calculation-methods#fifo)"
    out = rewrite_text(src, MAPPING)
    assert out == "[FIFO](/en/inventory/costing/calculation-methods#fifo)"


def test_does_not_touch_external_links():
    src = "[GitHub](https://github.com/foo/bar)"
    assert rewrite_text(src, MAPPING) == src


def test_does_not_touch_anchor_only_links():
    src = "[Section](#section-2)"
    assert rewrite_text(src, MAPPING) == src


def test_does_not_touch_relative_links():
    src = "[Sibling](./other-page.md) and [Parent](../sibling/page.md)"
    assert rewrite_text(src, MAPPING) == src


def test_ignores_paths_inside_fenced_code_block():
    src = (
        "Before [Costing](/en/costing/page).\n"
        "```\n"
        "Example URL: /en/costing/page\n"
        "[Looks like a link](/en/costing/page)\n"
        "```\n"
        "After [Costing](/en/costing/page).\n"
    )
    out = rewrite_text(src, MAPPING)
    # Outside fences: rewritten
    assert "Before [Costing](/en/inventory/costing/page)." in out
    assert "After [Costing](/en/inventory/costing/page)." in out
    # Inside fences: untouched
    assert "Example URL: /en/costing/page\n" in out
    assert "[Looks like a link](/en/costing/page)" in out


def test_ignores_paths_inside_tilde_fenced_block():
    src = (
        "~~~\n"
        "[Inside tilde fence](/en/costing/page)\n"
        "~~~\n"
    )
    assert rewrite_text(src, MAPPING) == src


def test_handles_multiple_links_on_one_line():
    src = "[A](/en/costing/a) and [B](/en/good-receive-note/b)"
    out = rewrite_text(src, MAPPING)
    assert out == (
        "[A](/en/inventory/costing/a) and [B](/en/inventory/good-receive-note/b)"
    )


def test_mapping_includes_all_three_prefixes_per_module():
    mapping = build_mapping(modules=["costing"], book="inventory")
    assert "/en/costing/" in mapping
    assert mapping["/en/costing/"] == "/en/inventory/costing/"
    assert "/th/costing/" in mapping
    assert mapping["/th/costing/"] == "/th/inventory/costing/"
    assert "/assets/screenshots/costing/" in mapping
    assert (
        mapping["/assets/screenshots/costing/"]
        == "/assets/screenshots/inventory/costing/"
    )


def test_does_not_rewrite_already_migrated_path():
    src = "[Already migrated](/en/inventory/costing/page)"
    assert rewrite_text(src, MAPPING) == src
