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


def test_collision_when_module_name_equals_book_name():
    # "inventory" is both a module slug and the book name. A naive pattern
    # /en/(?:inventory|costing|...)/.+ would falsely match the migrated
    # path /en/inventory/costing/page. The collision branch with a negative
    # lookahead on known module slugs must exclude migrated paths.
    modules = ["inventory", "costing", "good-receive-note"]
    patterns = build_stale_patterns(modules=modules, book="inventory")
    # Migrated paths must NOT be flagged
    assert find_stale_paths("[a](/en/inventory/costing/page)", patterns) == []
    assert find_stale_paths("[a](/en/inventory/inventory/page)", patterns) == []
    assert find_stale_paths("[a](/en/inventory/good-receive-note/page)", patterns) == []
    # Stale leftover under /en/inventory/ must still be flagged
    assert find_stale_paths(
        "[a](/en/inventory/some-old-page)", patterns
    ) == ["/en/inventory/some-old-page"]
    # And stale costing/grn under /en/ still flag
    assert find_stale_paths("[a](/en/costing/page)", patterns) == ["/en/costing/page"]


def test_book_home_link_not_flagged_as_stale():
    # /en/inventory/home is the book index page — legitimate post-migration target.
    modules = ["inventory", "costing", "good-receive-note"]
    patterns = build_stale_patterns(modules=modules, book="inventory")
    assert find_stale_paths("[a](/en/inventory/home)", patterns) == []
    assert find_stale_paths("[a](/th/inventory/home)", patterns) == []
    # But a stale leftover that happens to start with "home" should still flag.
    assert find_stale_paths(
        "[a](/en/inventory/home-old-page)", patterns
    ) == ["/en/inventory/home-old-page"]
