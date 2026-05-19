"""Tests for folder_moves.py."""
from scripts.migrate_books.folder_moves import generate_content_moves, generate_asset_moves


INVENTORY_MODULES = [
    "access-control", "costing", "dashboard", "good-receive-note",
    "inventory", "inventory-adjustment", "master-data", "physical-count",
    "product", "purchase-order", "purchase-request", "recipe",
    "reporting-audit", "spot-check", "store-requisition", "system-config",
    "templates", "vendor-pricelist",
]


def test_content_moves_includes_both_locales():
    moves = generate_content_moves(INVENTORY_MODULES, book="inventory")
    assert ("en/access-control", "en/inventory/access-control") in moves
    assert ("th/access-control", "th/inventory/access-control") in moves


def test_content_moves_count_equals_modules_times_locales():
    moves = generate_content_moves(INVENTORY_MODULES, book="inventory")
    assert len(moves) == len(INVENTORY_MODULES) * 2  # 18 × 2 = 36


def test_content_moves_does_not_move_inventory_module_into_itself():
    # "inventory" module name collides with new book name; ensure src/dst differ
    moves = generate_content_moves(INVENTORY_MODULES, book="inventory")
    pair = ("en/inventory", "en/inventory/inventory")
    assert pair in moves
    assert all(src != dst for src, dst in moves)


def test_asset_moves_includes_all_modules():
    moves = generate_asset_moves(INVENTORY_MODULES, book="inventory")
    assert ("assets/screenshots/costing", "assets/screenshots/inventory/costing") in moves
    assert len(moves) == len(INVENTORY_MODULES)


def test_format_as_git_mv_commands():
    from scripts.migrate_books.folder_moves import format_git_mv
    moves = [("en/foo", "en/inventory/foo"), ("th/foo", "th/inventory/foo")]
    output = format_git_mv(moves)
    assert "git mv en/foo en/inventory/foo" in output
    assert "git mv th/foo th/inventory/foo" in output
