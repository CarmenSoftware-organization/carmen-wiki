"""Rewrite root-relative markdown paths when content moves under a book folder.

Line-based scanner. Tracks fenced code blocks (``` and ~~~) and skips
their contents. Inside prose lines, rewrites occurrences of mapped path
prefixes that appear inside markdown link syntax `[text](path)` or
`![alt](path)`. External URLs (http(s):), relative paths (`./`, `../`),
and anchor-only fragments (`#x`) are not matched by the prefix patterns
and therefore left alone.
"""
from __future__ import annotations

import re
from pathlib import Path


_LINK_RE = re.compile(r"(!?\[[^\]]*\])\(([^)\s]+)\)")
_FENCE_RE = re.compile(r"^(\s*)(```|~~~)")


def build_mapping(*, modules: list[str], book: str) -> dict[str, str]:
    """Build the prefix→prefix mapping for one book's modules.

    Returns three entries per module (EN, TH, assets) — all trailing-slashed
    so we never partial-match e.g. /en/costing-other/.
    """
    m: dict[str, str] = {}
    for module in modules:
        m[f"/en/{module}/"] = f"/en/{book}/{module}/"
        m[f"/th/{module}/"] = f"/th/{book}/{module}/"
        m[f"/assets/screenshots/{module}/"] = (
            f"/assets/screenshots/{book}/{module}/"
        )
    return m


def _rewrite_path(path: str, mapping: dict[str, str]) -> str:
    """Apply the first matching prefix; preserve fragment/query.

    The current mapping has no shadowing (no prefix is a prefix of another),
    so first-match and longest-match are equivalent.
    """
    for src_prefix, dst_prefix in mapping.items():
        if path.startswith(src_prefix):
            return dst_prefix + path[len(src_prefix):]
    return path


def rewrite_text(text: str, mapping: dict[str, str]) -> str:
    """Rewrite all mapped link/image paths in `text`, skipping code fences."""
    out_lines: list[str] = []
    in_fence = False
    fence_marker: str | None = None
    for line in text.splitlines(keepends=True):
        fence_match = _FENCE_RE.match(line)
        if fence_match:
            marker = fence_match.group(2)
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
                fence_marker = None
            out_lines.append(line)
            continue
        if in_fence:
            out_lines.append(line)
            continue

        def _sub(match: re.Match[str]) -> str:
            label = match.group(1)
            path = match.group(2)
            return f"{label}({_rewrite_path(path, mapping)})"

        out_lines.append(_LINK_RE.sub(_sub, line))
    return "".join(out_lines)


def rewrite_file(path: Path, mapping: dict[str, str]) -> bool:
    """Rewrite a single markdown file in place. Returns True if changed."""
    original = path.read_text(encoding="utf-8")
    updated = rewrite_text(original, mapping)
    if updated == original:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def main() -> None:
    """Walk en/ and th/ markdown files and apply the inventory mapping."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Rewrite root-relative paths after multi-book restructure.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report files that would change without writing.",
    )
    args = parser.parse_args()

    inventory_modules = [
        "access-control", "costing", "dashboard", "good-receive-note",
        "inventory", "inventory-adjustment", "master-data", "physical-count",
        "product", "purchase-order", "purchase-request", "recipe",
        "reporting-audit", "spot-check", "store-requisition", "system-config",
        "templates", "vendor-pricelist",
    ]
    mapping = build_mapping(modules=inventory_modules, book="inventory")

    repo_root = Path(__file__).resolve().parent.parent.parent
    changed = 0
    scanned = 0
    for md in list(repo_root.glob("en/**/*.md")) + list(repo_root.glob("th/**/*.md")):
        scanned += 1
        if args.dry_run:
            original = md.read_text(encoding="utf-8")
            updated = rewrite_text(original, mapping)
            if updated != original:
                changed += 1
                print(f"WOULD REWRITE: {md.relative_to(repo_root)}")
        else:
            if rewrite_file(md, mapping):
                changed += 1
                print(f"REWROTE: {md.relative_to(repo_root)}")
    verb = "would be changed" if args.dry_run else "changed"
    print(f"\n{changed} of {scanned} markdown files {verb}.")


if __name__ == "__main__":
    main()
