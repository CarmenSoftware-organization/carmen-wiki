# Folder-Name Default Pages — Switch From `index.md` To Sibling `<folder>.md`

**Date:** 2026-05-19
**Status:** Draft (awaiting spec review)
**Scope:** all `index.md` files under `en/` and `th/` (54 files), plus `scripts/sync_nav.py`, `scripts/nav-overrides.yaml`, `README.md`, `CLAUDE.md`, and the small number of relative `index.md` back-links in Inventory sub-pages and Platform single-page modules

## Goal

Make the per-folder default landing page resolve to the **folder's own URL** in Wiki.js — `/en/inventory`, `/en/inventory/costing`, `/en` — by moving every `<folder>/index.md` up one level and renaming it to `<folder>.md`. The two locale roots (`en/index.md`, `th/index.md`) move to `en.md` and `th.md` at the repo root.

## Why

The previous design (commit `de12ba6`, "rename `home.md` → `index.md` at all levels") standardized on `index.md` to give every level a single filename. In practice the Wiki.js URLs that come out of this convention are `/en/index`, `/en/inventory/index`, `/en/inventory/costing/index` — the literal filename appears in the URL. The user observed that visitors landing on the language root see `/en/home` (legacy cache) or `/en/index` (current state) rather than the clean `/en` they expect.

The Wiki.js Git-storage path → URL contract is straightforward: a file at `<path>.md` becomes URL `<path>`. The only way to make `/en/inventory` the canonical URL of the Inventory book landing is to place the file at `en/inventory.md` — as a **sibling** of the `en/inventory/` folder, not inside it. This is the Hugo / MkDocs "page bundle" pattern.

Standardizing on this pattern eliminates the `/index` URL suffix everywhere, makes folder URLs the canonical reading paths, and lets the Wiki.js admin "Default Path" setting be `/en` (matching the `en.md` file) without further indirection.

## Non-goals

- Changing any **content** of the landing pages. This is a rename + link-update refactor only. The Inventory and Platform module landings keep their text verbatim.
- Restructuring sub-pages. Module folders still contain their `01-data-model.md`, `02-business-rules.md`, role-specific user-flow / test-scenario files, etc. — those stay in place.
- Renaming any non-`index.md` files. `calculation-methods.md`, `category.md`, `wastage-reporting.md` and similar already-leaf files are untouched.
- Updating historical references inside `docs/superpowers/plans/*.md` and `docs/superpowers/specs/*.md`. These are snapshots and stay as written.
- Changing Wiki.js theme, plugins, or the storage backend itself.

## Constraints

- **`scripts/sync_nav.py` is global.** It hardcodes `INDEX_MD = "index.md"` (line 102) and reads `repo_root / "en" / "index.md"`, `repo_root / "th" / "index.md"` (lines 397–398, 467–468) directly to harvest section headings for the sidebar label map. After the rename these paths become `repo_root / "en.md"`, `repo_root / "th.md"`. The script must be updated atomically with the file renames or the nav build breaks.
- **`scripts/nav-overrides.yaml` carries `home_slug: index`** for both books. The script appends `home_slug` to the URL (`/{locale}/{book_slug}/{home_slug}` and `/{locale}/{book_slug}/{module}/{home_slug}`). After the rename, the canonical URLs are `/{locale}/{book_slug}` and `/{locale}/{book_slug}/{module}` — no trailing slug. The simplest fix is to remove the `home_slug` field and the URL-construction segment that appends it.
- **`resolve_th_page_title` (lines 77–93)** already tries both `<rel>.md` and `<rel>/index.md` as fallback. The first form already matches the new convention. The second form becomes dead code but is harmless — leave it for backward compatibility during the cache window, or remove it. The implementation plan decides.
- **Wiki.js admin "Default Path"** at `dev.blueledgers.com:3987` is configured through the admin UI, not this repo. It must be set to `/en` once renames are deployed.
- **Internal `[[wiki-style]]` links** use slugs without a filename component (`[[costing/calculation-methods]]`), so they need no change. Only **explicit URL-style and relative-Markdown** links need updates.
- **Platform single-page modules (`auth-roles`, `profile`)** contain a relative link `[Platform book index](../index.md)` that resolves to `en/platform/index.md` today. After the rename, the link target moves to `en/platform.md` — the relative path becomes `../platform.md` or absolute `/en/platform`. Updated as part of this work.
- **Inventory sub-pages with back-links** — several PR/PO/vendor-pricelist user-flow files contain `[index.md](./index.md)` relative back-links to the module landing. After the rename, the module landing is a sibling of the sub-page's folder, so `./index.md` becomes `../<module>.md` or absolute `/en/inventory/<module>`.

## Decisions

| Decision | Choice | Why |
|---|---|---|
| Filename convention | `<folder>.md` placed as a sibling of `<folder>/` at every level | Only convention in Wiki.js Git storage that yields clean folder URLs without a filename suffix. User-stated goal. |
| Locale root | `en.md`, `th.md` at repo root (sibling of `en/` and `th/`) | Same pattern applied consistently. URLs are `/en`, `/th`. |
| `home_slug` in `nav-overrides.yaml` | Remove the field; remove the URL segment that appends it | After the rename the URL has no trailing slug. Keeping `home_slug: ""` and appending it would produce `/en/inventory/` with a trailing slash — Wiki.js normalizes but the config becomes a footgun. |
| Internal back-link style for sub-pages | Absolute URLs (`/en/inventory/<module>`) | Survives any further moves; matches the style already used in landing pages (`/en/inventory/<module>/index`). |
| Old `index.md` fallback in `resolve_th_page_title` | Leave the second candidate path in place | Defensive — harmless dead code, and pages cached by Wiki.js with old paths may still resolve during the transition. |
| `verify.py` skip patterns | Leave untouched | The `home` pattern in `migrate_books/verify.py` is for the one-shot historical multi-book migration; it doesn't affect ongoing work. |
| Commit strategy | Single atomic structural commit on a feature branch, then PR | Wiki.js git storage syncs the whole tree on push; a partial commit would leave the wiki broken. The rename has no natural sub-units to stage. |
| TH parity | TH renames and link updates in the same commit as EN | The wiki is bilingual; shipping EN-only would leave TH sidebar broken. |
| Old plans/specs | Not updated | Historical records of completed work. |

## Unit decomposition

One atomic commit on branch `feat/folder-name-pages`. Below is what that commit contains.

### File renames — 54 files (use `git mv` to preserve history)

**Locale roots (2):**

| Old path | New path |
|---|---|
| `en/index.md` | `en.md` |
| `th/index.md` | `th.md` |

**Book landings (4):**

| Old path | New path |
|---|---|
| `en/inventory/index.md` | `en/inventory.md` |
| `en/platform/index.md` | `en/platform.md` |
| `th/inventory/index.md` | `th/inventory.md` |
| `th/platform/index.md` | `th/platform.md` |

**Inventory module landings (36):** for each of 18 modules in `en/inventory/` and the same 18 in `th/inventory/`:
`{en,th}/inventory/<module>/index.md` → `{en,th}/inventory/<module>.md`

Modules (alphabetical): `access-control`, `costing`, `dashboard`, `good-receive-note`, `inventory`, `inventory-adjustment`, `master-data`, `physical-count`, `product`, `purchase-order`, `purchase-request`, `recipe`, `reporting-audit`, `spot-check`, `store-requisition`, `system-config`, `templates`, `vendor-pricelist`.

**Platform module landings (12):** for each of 6 modules in `en/platform/` and the same 6 in `th/platform/`:
`{en,th}/platform/<module>/index.md` → `{en,th}/platform/<module>.md`

Modules: `auth-roles`, `business-units`, `clusters`, `profile`, `report-templates`, `users`.

### URL updates inside renamed files

Drop the `/index` suffix in absolute links.

| File | Pattern to replace | Replacement | Approx. count |
|---|---|---|---|
| `en.md`, `th.md` | `(/en\|/th)/(inventory\|platform)/index` | `(/en\|/th)/(inventory\|platform)` | 2 URLs per file × 2 files = 4 |
| `en/inventory.md`, `th/inventory.md` | `(/en\|/th)/inventory/<module>/index` | `(/en\|/th)/inventory/<module>` | ~18 URLs per file × 2 files ≈ 36 |
| `en/platform.md`, `th/platform.md` | `(/en\|/th)/platform/<module>/index` | `(/en\|/th)/platform/<module>` | ~6 URLs per file × 2 files = 12 |

### Back-link updates in sub-pages

Files with `[index.md](./index.md)` relative back-links (purchase-order user-flows, purchase-request user-flows, vendor-pricelist user-flows — both EN and TH). Replace pattern with absolute link to the module landing, **and rewrite the link text** so the sentence still reads naturally — `[index.md](./index.md)` is the *file* of the module landing, not the topic, so substituting the folder name reads awkwardly.

- From `en/inventory/purchase-order/03-user-flow.md` (and similar):
  - Before: `The role catalogue itself is defined in [index.md](./index.md) Section 4.`
  - After: `The role catalogue itself is defined in [the module landing](/en/inventory/purchase-order) Section 4.`
- TH counterparts replace with the Thai equivalent text and the `/th/...` URL:
  - Before: `แค็ตตาล็อก role อยู่ที่ [index.md](./index.md) Section 4`
  - After: `แค็ตตาล็อก role อยู่ที่ [หน้าหลักโมดูล](/th/inventory/purchase-order) Section 4`

The implementation plan decides whether to do the rewrite mechanically (single regex per locale) or per-file (slightly more graceful phrasing). Either is acceptable.

**Special case — Platform single-page modules:**

| File | Before | After |
|---|---|---|
| `en/platform/auth-roles.md` (was `auth-roles/index.md`) | `[Platform book index](../index.md)` | `[Platform book index](/en/platform)` |
| `en/platform/profile.md` | `[Platform book index](../index.md)` | `[Platform book index](/en/platform)` |
| `th/platform/auth-roles.md` | `[สารบัญหนังสือ Platform](../index.md)` | `[สารบัญหนังสือ Platform](/th/platform)` |
| `th/platform/profile.md` | `[สารบัญหนังสือ Platform](../index.md)` | `[สารบัญหนังสือ Platform](/th/platform)` |

### Script and config updates

**`scripts/nav-overrides.yaml`:** remove the `home_slug: index` line under both `inventory:` and `platform:`.

**`scripts/sync_nav.py`:**

| Line | Before | After |
|---|---|---|
| 102 | `INDEX_MD = "index.md"` | Remove (no longer needed) **or** keep for any remaining `parse_index_headings` call signature compatibility — implementation plan decides |
| 30, 38, 46 | `parse_index_headings(index_md: Path)` reads `index_md` | Function signature/usage unchanged — just gets called with `en.md` / `th.md` paths |
| 87 | `repo_root / rel / "index.md"` (fallback in `resolve_th_page_title`) | Leave as defensive fallback |
| 377 | `f"·  {counts.get('index.md', 0)} index.md  "` | `f"·  {counts.get('landing', 0)} landings  "` or similar — cosmetic only |
| 397–398 | `parse_index_headings(repo_root / "en" / "index.md")` | `parse_index_headings(repo_root / "en.md")` |
| 467–468 | Same as 397–398 | Same fix |
| 664 | `home_slug = book.get("home_slug", "index")` | Remove |
| 668 | `f"/{locale}/{book_slug}/{home_slug}"` | `f"/{locale}/{book_slug}"` |
| 677 | `f"/{locale}/{book_slug}/{module['slug']}/{home_slug}"` | `f"/{locale}/{book_slug}/{module['slug']}"` |

**`scripts/test_sync_nav.py`:** any test fixtures referencing `en/index.md` or the `/index` URL suffix must be updated alongside the production change. Run `pytest scripts/` to confirm.

### Doc updates

**`README.md`:**

| Line | Update |
|---|---|
| 17 | `│   ├── index.md           # Wiki landing page (book index)` → `│   ├── <book>.md         # Book landing page (sibling of <book>/)` |
| 19 | `│   │   ├── index.md       # Module landing page` → `│   │   ├── <module>.md   # Module landing (sibling of <module>/)` |
| 43 | Update the `index.md` row in the page-types table to `<module>.md` |

**`CLAUDE.md`** (line 15):
- "The language-root pages `en/index.md` and `th/index.md` are the two-card landings; each book has its own `<book>/index.md` page that opens the book."
  → "The language-root pages `en.md` and `th.md` (siblings of `en/` and `th/`) are the two-card landings; each book has its own `<book>.md` sibling page that opens the book."

## Verification

1. `pytest scripts/` passes (test_sync_nav fixtures updated to match new paths and URLs).
2. `python scripts/sync_nav.py --mode=build --dry-run` (or whatever no-op mode the script supports) runs without error and prints book URLs without `/index` suffix.
3. `grep -rE "/(home|index)\b" en/ th/ --include="*.md"` returns zero hits (a tail of historical Wiki-style references in old plan/spec files is acceptable; current content must be clean).
4. `grep -rn "home\.md\|/index\b" scripts/sync_nav.py scripts/nav-overrides.yaml README.md CLAUDE.md` returns zero hits.
5. `find en th -type f -name "index.md"` returns no files.
6. Push to `dev.blueledgers.com:3987` and open in browser:
   - `/en` loads the Carmen Wiki two-card landing
   - `/th` loads the Thai two-card landing
   - `/en/inventory` loads the Inventory book home
   - `/en/platform` loads the Platform book home
   - `/en/inventory/costing` loads the Costing module home
   - `/en/inventory/purchase-order` loads the PO module home (and the back-link from `03-user-flow.md` to the module landing resolves)
   - `/en/platform/profile` loads the Profile single-page (and the back-link to `/en/platform` resolves)
   - Spot-check the same paths under `/th/...`
7. Wiki.js admin → Site Settings → "Default Path" → set to `/en`. Manual step, must be checked off explicitly during deploy.
8. Sidebar still renders both books with their group headers; clicking the book home link goes to `/en/inventory` (not `/en/inventory/index`).

## Risks and open items

| Risk | Mitigation |
|---|---|
| Wiki.js "Default Path" admin setting still points to `/en/home` or `/en/index` after deploy → `/` returns 404 | Verification step 7 is explicit and manual; flag in deploy notes. |
| Wiki.js page cache still serves the old `/en/inventory/index` URL until TTL expires | Acceptable. Admin can flush cache, or wait. Document in deploy notes. |
| Wiki.js git storage may not detect file renames as renames (treats as delete-then-create) → page edit history breaks for the landing files | Use `git mv` and let Wiki.js re-index; the file-history loss is bounded to the 54 landing files and is acceptable. |
| Two side-by-side landings on disk look unusual to a future contributor: `en/inventory.md` alongside `en/inventory/` folder | Document the convention in `README.md` and `CLAUDE.md` (covered above). |
| Locale roots at repo root (`en.md`, `th.md`) crowd the top-level directory | Acceptable — only 2 files added; the locale folders themselves keep all other content. |
| Sub-page back-links updated to absolute paths assume the URL convention won't change again | Acceptable. If it changes again, a single grep-replace can update them all. |

## Out of scope (explicit)

- Updating any file under `docs/superpowers/plans/` or `docs/superpowers/specs/` to reflect the new URL convention. These are historical snapshots.
- Touching `scripts/migrate_books/verify.py` skip patterns (historical, not in active use).
- Adding new pages or modules to either book.
- Changing the `tags` taxonomy, frontmatter fields, or template structure.
- Re-translating any Thai content.
- Wiki.js theme, plugin, storage backend, or routing changes beyond the one admin "Default Path" setting.
