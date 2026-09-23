#!/usr/bin/env python3
"""Embed screenshots into EN and TH wiki pages by path convention.

Spec: docs/superpowers/specs/2026-09-23-screenshots-all-books-design.md §2, §5.1.

  assets/screenshots/<book>/<module>/index.png            -> <loc>/<book>/<module>.md
  assets/screenshots/<book>/<module>/<slug>.png           -> <loc>/<book>/<module>/<slug>.md
  assets/screenshots/<book>/<module>/<slug>-<variant>.png -> same page as <slug> (exact page name wins)

Idempotent: a URL already present in a page is never inserted again.
"""
import argparse, datetime, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets" / "screenshots"
LOCALES = ("en", "th")
URL_PREFIX = {"inventory": "/screenshots", "platform": "/screenshots/platform"}
SKIP_NAME = re.compile(r"(data-model|business-rules|test-scenarios|user-flow|permissions)")
SKIP_PAGES = {
    "inventory/costing", "inventory/costing/calculation-methods",
    "inventory/general-ledger/gl-posting", "inventory/system-config/doc-version",
    "platform/users/lifecycle", "platform/report-templates/xml-spec",
}
CHANGED_LIST = Path("/private/tmp/claude-501/embed-changed.txt")


def page_exists(rel: str) -> bool:
    return (ROOT / "en" / f"{rel}.md").is_file()


def resolve(book: str, module: str, stem: str) -> tuple[str, str | None] | None:
    """Map an image to (page_rel, variant); page_rel is '<book>/<module>[/<slug>]'."""
    if "--" in stem:  # role-suffixed catalog shot, never embedded
        return None
    if stem == "index" or stem.startswith("index-"):
        rel = f"{book}/{module}"
        return (rel, stem[len("index-"):] or None) if page_exists(rel) else None
    exact = f"{book}/{module}/{stem}"
    if page_exists(exact):
        return (exact, None)
    parts = stem.split("-")
    for i in range(len(parts) - 1, 0, -1):  # longest prefix first
        rel = f"{book}/{module}/{'-'.join(parts[:i])}"
        if page_exists(rel):
            return (rel, "-".join(parts[i:]))
    return None


def title_of(text: str) -> str:
    m = re.search(r"^title:\s*(.+)$", text, re.M)
    return m.group(1).strip().strip("'\"") if m else ""


def insert_at(lines: list[str]) -> int:
    """Index before which the image line goes (spec §5.1 placement)."""
    fm_end = lines.index("---", 1)
    body = range(fm_end + 1, len(lines))
    glance = next((i for i in body if lines[i].startswith("> **At a Glance**")), None)
    if glance is not None:
        i = glance
        while i < len(lines) and lines[i].startswith(">"):
            i += 1
    else:
        first_section = next((i for i in body if re.match(r"^## 1\.", lines[i])), None)
        if first_section is not None:
            return first_section
        i = next((j + 1 for j in body if lines[j].startswith("# ")), fm_end + 1)
    # Keep images grouped: step over blank lines and images already placed here.
    while i < len(lines) and (lines[i].strip() == "" or lines[i].startswith("![")):
        i += 1
    return i


def embed(page: Path, url: str, variant: str | None, now: str) -> bool:
    text = page.read_text(encoding="utf-8")
    if f"]({url})" in text:
        return False
    alt = title_of(text) + (f" {variant.replace('-', ' ')}" if variant else "") + " screen"
    lines = text.split("\n")
    at = insert_at(lines)
    lines[at:at] = [f"![{alt}]({url})", ""]
    out = re.sub(r"^date:.*$", f"date: {now}", "\n".join(lines), count=1, flags=re.M)
    page.write_text(out, encoding="utf-8")
    return True


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--book", choices=sorted(URL_PREFIX))
    args = ap.parse_args(argv)
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    inserts = skips = 0
    changed: set[str] = set()
    for book in [args.book] if args.book else sorted(URL_PREFIX):
        # Base image before its variants: "ui-screens" must sort ahead of "ui-screens-form".
        for png in sorted((ASSETS / book).glob("*/*.png"), key=lambda p: (p.parent.name, p.stem.replace("-", "\x7f"))):
            module, stem = png.parent.name, png.stem
            hit = resolve(book, module, stem)
            if not hit:
                print(f"- {png.relative_to(ROOT)}  no matching page")
                skips += 1
                continue
            rel, variant = hit
            if rel in SKIP_PAGES or SKIP_NAME.search(rel.rsplit("/", 1)[-1]):
                print(f"- {png.relative_to(ROOT)}  out-of-scope page {rel}")
                skips += 1
                continue
            url = f"{URL_PREFIX[book]}/{module}/{png.name}"
            for loc in LOCALES:
                page = ROOT / loc / f"{rel}.md"
                if not page.is_file():
                    print(f"! {loc}/{rel}.md missing (image {url})")
                    continue
                if f"]({url})" in page.read_text(encoding="utf-8"):
                    continue
                print(f"+ {loc}/{rel}.md  {url}")
                inserts += 1
                if not args.dry_run and embed(page, url, variant, now):
                    changed.add(f"{loc}/{rel}.md")
    if not args.dry_run:
        CHANGED_LIST.parent.mkdir(parents=True, exist_ok=True)
        CHANGED_LIST.write_text("".join(f"{p}\n" for p in sorted(changed)))
    verb = "planned" if args.dry_run else "inserted"
    print(f"---- {verb} {inserts}, skipped images {skips}, pages changed {len(changed)} ----")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
