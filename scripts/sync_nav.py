"""Sync Wiki.js TH locale navigation from EN locale.

See docs/superpowers/specs/2026-05-18-th-navigation-design.md for design.
"""
from __future__ import annotations

import argparse
from enum import Enum
import logging
import os
import re
import sys
import uuid
from pathlib import Path
from typing import Any

import frontmatter
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
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


# ===== Section 8: Wiki.js GraphQL =====

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


def _make_client(api_url: str, api_token: str) -> Client:
    transport = RequestsHTTPTransport(
        url=api_url,
        headers={"Authorization": f"Bearer {api_token}"},
        retries=2,
        timeout=30,
    )
    return Client(transport=transport, fetch_schema_from_transport=False)


def fetch_navigation(api_url: str, api_token: str) -> dict[str, Any]:
    """Fetch the full navigation tree + config mode.

    Returns the raw `navigation` payload: {tree: [...], config: {mode: ...}}.
    """
    client = _make_client(api_url, api_token)
    result = client.execute(_QUERY_NAVIGATION)
    return result["navigation"]


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


# ===== Section 9: Reporting =====


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


# ===== Section 10: Orchestration =====


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


# ===== Section 11: CLI =====


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(message)s",
        stream=sys.stderr,
    )


def _run_mirror_mode(
    *,
    api_url: str,
    api_token: str,
    repo_root: Path,
    overrides_path: Path,
    dry_run: bool,
    verbose: bool,
) -> int:
    """Fetch EN nav from Wiki.js, derive TH, push TH (existing behavior)."""
    # 1. fetch
    print(f"[FETCH]  api={api_url}", file=sys.stderr)
    nav = fetch_navigation(api_url, api_token)
    try:
        assert_static_mode(nav)
    except SystemExit as e:
        print(str(e), file=sys.stderr)
        return 4
    tree = nav.get("tree") or []
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

    if verbose:
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

    if dry_run:
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


def _run_build_mode(
    *,
    api_url: str,
    api_token: str,
    overrides_path: Path,
    dry_run: bool,
) -> int:
    config = yaml.safe_load(overrides_path.read_text(encoding="utf-8")) or {}
    if not config.get("books"):
        print(
            "ERROR: nav-overrides.yaml has no `books:` block; cannot build.",
            file=sys.stderr,
        )
        return 5

    en_items = build_tree_from_config(config, locale="en")
    th_items = build_tree_from_config(config, locale="th")
    print(
        f"[BUILD]  en: {len(en_items)} items, th: {len(th_items)} items",
        file=sys.stderr,
    )

    new_tree = [
        {"locale": "en", "items": en_items},
        {"locale": "th", "items": th_items},
    ]

    if dry_run:
        print("[DRY-RUN] tree preview:", file=sys.stderr)
        for locale_tree in new_tree:
            print(f"  {locale_tree['locale']}:", file=sys.stderr)
            for item in locale_tree["items"]:
                print(f"    {item['kind']:<8} {item.get('label', ''):<40} {item.get('target', '')}", file=sys.stderr)
        print("[DRY-RUN] no mutation sent.", file=sys.stderr)
        return 0

    # In build mode, we don't preserve other locales — Wiki.js currently
    # only has en + th, and build mode is the source of truth.
    push_navigation(api_url, api_token, new_tree)
    print("[PUSH]   updateTree succeeded.", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Manage Wiki.js navigation tree.",
    )
    parser.add_argument(
        "--mode",
        choices=["mirror", "build"],
        default="mirror",
        help=(
            "mirror (default): fetch EN from Wiki.js, derive and push TH only. "
            "build: rebuild EN + TH from nav-overrides.yaml books: block."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute + print; do not push.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-item resolution lines (mirror mode only).",
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

    if args.mode == "build":
        return _run_build_mode(
            api_url=api_url,
            api_token=api_token,
            overrides_path=overrides_path,
            dry_run=args.dry_run,
        )
    return _run_mirror_mode(
        api_url=api_url,
        api_token=api_token,
        repo_root=repo_root,
        overrides_path=overrides_path,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )


# ===== Section 10b: Declarative tree builder (build mode) =====


def _new_link(label: str, target: str) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "kind": "link",
        "label": label,
        "icon": "",
        "targetType": "page",
        "target": target,
        "visibilityMode": "all",
        "visibilityGroups": [],
    }


def _new_header(label: str) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "kind": "header",
        "label": label,
        "icon": "",
        "targetType": "none",
        "target": "",
        "visibilityMode": "all",
        "visibilityGroups": [],
    }


def _new_divider() -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "kind": "divider",
        "label": "",
        "icon": "",
        "targetType": "none",
        "target": "",
        "visibilityMode": "all",
        "visibilityGroups": [],
    }


def build_tree_from_config(
    config: dict[str, Any],
    *,
    locale: str,
) -> list[dict[str, Any]]:
    """Build a Wiki.js nav tree for one locale from the books: config block.

    For each book: emit a book header, a link to /<locale>/<book>/<home_slug>,
    then for each group: emit a group header followed by a link per module
    pointing to /<locale>/<book>/<module>/<home_slug>. A divider separates
    consecutive books.
    """
    label_key = f"label_{locale}"
    items: list[dict[str, Any]] = []
    books = config.get("books") or {}
    for idx, (book_slug, book) in enumerate(books.items()):
        if idx > 0:
            items.append(_new_divider())
        items.append(_new_header(book[label_key]))
        home_slug = book.get("home_slug", "home")
        items.append(
            _new_link(
                "Home",
                f"/{locale}/{book_slug}/{home_slug}",
            )
        )
        for group in book.get("groups") or []:
            items.append(_new_header(group[label_key]))
            for module in group.get("modules") or []:
                items.append(
                    _new_link(
                        module[label_key],
                        f"/{locale}/{book_slug}/{module['slug']}/{home_slug}",
                    )
                )
    return items


if __name__ == "__main__":
    sys.exit(main())
