# scripts/migrate_books/

One-shot tooling for the multi-book restructure
(`docs/superpowers/specs/2026-05-19-multi-book-restructure-design.md`).

Run order:
1. `folder_moves.py` — print `git mv` commands; pipe to `bash` after review
2. `rewrite_links.py` — rewrite root-relative paths in markdown
3. `scaffold_platform.py` — generate Platform book skeleton pages
4. `verify.py` — assert no old paths remain

After the PR merges, this package can be deleted; it is not part of
day-to-day wiki workflows.
