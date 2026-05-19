"""Tests for verify.py."""
from scripts.migrate_books.verify import find_stale_paths, build_stale_patterns


INVENTORY_MODULES = ["costing", "good-receive-note"]


def test_stale_patterns_match_unmigrated_path():
    patterns = build_stale_patterns(modules=INVENTORY_MODULES, book="inventory")
    src = "[link](/en/costing/page)"
    assert find_stale_paths(src, patterns) == ["/en/costing/page"]


def test_no_false_positive_on_migrated_path():
    patterns = build_stale_patterns(modules=INVENTORY_MODULES, book="inventory")
    src = "[link](/en/inventory/costing/page)"
    assert find_stale_paths(src, patterns) == []


def test_finds_stale_asset_reference():
    patterns = build_stale_patterns(modules=INVENTORY_MODULES, book="inventory")
    src = "![grn](/assets/screenshots/good-receive-note/x.png)"
    assert find_stale_paths(src, patterns) == [
        "/assets/screenshots/good-receive-note/x.png"
    ]


def test_finds_multiple_in_one_text():
    patterns = build_stale_patterns(modules=INVENTORY_MODULES, book="inventory")
    src = "[a](/en/costing/x) and [b](/th/good-receive-note/y)"
    result = find_stale_paths(src, patterns)
    assert "/en/costing/x" in result
    assert "/th/good-receive-note/y" in result
