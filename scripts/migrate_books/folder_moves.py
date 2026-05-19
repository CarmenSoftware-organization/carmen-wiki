"""Generate `git mv` plans for moving content and assets under book folders.

Pure functions; this module performs no filesystem changes. Callers pipe
`format_git_mv()` output to `bash` after review.
"""
from __future__ import annotations


def generate_content_moves(
    modules: list[str],
    *,
    book: str,
    locales: tuple[str, ...] = ("en", "th"),
) -> list[tuple[str, str]]:
    """Return list of (src, dst) pairs for content folder moves.

    For each module M and locale L: <L>/<M>  ->  <L>/<book>/<M>
    """
    moves: list[tuple[str, str]] = []
    for locale in locales:
        for module in modules:
            src = f"{locale}/{module}"
            dst = f"{locale}/{book}/{module}"
            moves.append((src, dst))
    return moves


def generate_asset_moves(
    modules: list[str],
    *,
    book: str,
    assets_root: str = "assets/screenshots",
) -> list[tuple[str, str]]:
    """Return list of (src, dst) pairs for asset folder moves.

    For each module M: <assets_root>/<M>  ->  <assets_root>/<book>/<M>
    """
    return [
        (f"{assets_root}/{m}", f"{assets_root}/{book}/{m}")
        for m in modules
    ]


def format_git_mv(moves: list[tuple[str, str]]) -> str:
    """Format moves as a bash-compatible series of `git mv` commands."""
    return "\n".join(f"git mv {src} {dst}" for src, dst in moves) + "\n"


def main() -> None:
    """Print the full folder-move plan to stdout for review."""
    inventory_modules = [
        "access-control", "costing", "dashboard", "good-receive-note",
        "inventory", "inventory-adjustment", "master-data", "physical-count",
        "product", "purchase-order", "purchase-request", "recipe",
        "reporting-audit", "spot-check", "store-requisition", "system-config",
        "templates", "vendor-pricelist",
    ]
    content_moves = generate_content_moves(inventory_modules, book="inventory")
    asset_moves = generate_asset_moves(inventory_modules, book="inventory")
    print("# Content moves")
    print(format_git_mv(content_moves), end="")
    print()
    print("# Asset moves")
    print(format_git_mv(asset_moves), end="")


if __name__ == "__main__":
    main()
