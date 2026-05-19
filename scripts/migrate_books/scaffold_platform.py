"""Generate Platform book skeleton pages from a YAML config.

Each page has:
- Wiki.js YAML frontmatter (title, description, tags, dates, editor)
- ## 1. At a Glance      -- bulleted preview of intended subtopics
- ## 2. References       -- bulleted links/paths to source-of-truth files
- ## 3. TODO             -- bulleted checklist for the author
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import yaml


@dataclass
class PageSpec:
    path: str            # relative to <locale>/<book>/  e.g. "clusters/index.md"
    title_en: str
    title_th: str
    description: str
    tags: list[str]
    at_a_glance: list[str]
    references: list[str]
    todo: list[str]


def iter_pages(yaml_path: Path) -> Iterator[PageSpec]:
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    for raw in data["pages"]:
        yield PageSpec(
            path=raw["path"],
            title_en=raw["title_en"],
            title_th=raw["title_th"],
            description=raw["description"],
            tags=list(raw.get("tags") or []),
            at_a_glance=list(raw.get("at_a_glance") or []),
            references=list(raw.get("references") or []),
            todo=list(raw.get("todo") or []),
        )


def render_page(spec: PageSpec, *, locale: str, today_iso: str) -> str:
    title = spec.title_en if locale == "en" else spec.title_th
    tags = ", ".join(spec.tags)
    front = (
        "---\n"
        f"title: {title}\n"
        f"description: {spec.description}\n"
        "published: true\n"
        f"date: '{today_iso}'\n"
        f"tags: {tags}\n"
        "editor: markdown\n"
        f"dateCreated: '{today_iso}'\n"
        "---\n\n"
    )
    glance = "## 1. At a Glance\n\n" + "\n".join(f"- {b}" for b in spec.at_a_glance) + "\n\n"
    refs = "## 2. References\n\n" + "\n".join(f"- {r}" for r in spec.references) + "\n\n"
    todo = "## 3. TODO\n\n" + "\n".join(f"- [ ] {t}" for t in spec.todo) + "\n"
    return front + f"# {title}\n\n" + glance + refs + todo


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate Platform book skeleton pages."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).resolve().parent / "platform_pages.yaml",
    )
    parser.add_argument(
        "--locales",
        nargs="+",
        default=["en", "th"],
    )
    parser.add_argument(
        "--today",
        default="2026-05-19T00:00:00.000Z",
        help="ISO timestamp used for date / dateCreated.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files (skip otherwise).",
    )
    args = parser.parse_args()

    book = "platform"
    repo_root = Path(__file__).resolve().parent.parent.parent
    created = 0
    skipped = 0

    for spec in iter_pages(args.config):
        for locale in args.locales:
            dst = repo_root / locale / book / spec.path
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists() and not args.force:
                skipped += 1
                print(f"SKIP (exists): {dst.relative_to(repo_root)}")
                continue
            dst.write_text(render_page(spec, locale=locale, today_iso=args.today), encoding="utf-8")
            created += 1
            print(f"WROTE: {dst.relative_to(repo_root)}")
    print(f"\n{created} created, {skipped} skipped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
