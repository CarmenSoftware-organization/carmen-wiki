# Multi-Book Restructure — Design

**Date:** 2026-05-19
**Status:** Approved
**Approach:** Big-bang (single PR)

## Goal

Convert `carmen-wiki` from a single-product wiki (Inventory only) into a multi-book platform wiki served by one Wiki.js instance. Introduce two top-level books:

- **Carmen Inventory** — all existing content (18 modules × 2 locales, ~442 pages)
- **Carmen Platform** — new skeleton sourced from `../carmen-platform/` (6 modules, ~17 pages per locale × 2 locales = ~34 skeleton pages, plus 2 book-home pages)

The design must:
- Preserve git history of moved files (use `git mv`)
- Keep Wiki.js as the rendering engine; no theme or engine changes
- Update every internal link and image reference to the new paths
- Extend `scripts/sync_nav/` to drive a two-book Wiki.js sidebar
- Stay shippable in a single feature branch + PR

## Constraints

- Wiki.js instance is shared (`http://dev.blueledgers.com:3987/`); content is git-stored and synced
- Content audience stays the same (developers + testers); skeleton-only Platform content is acceptable for now
- EN and TH locale trees must mirror each other
- Existing conventions (numbered sections, Wiki.js YAML frontmatter, root-relative `/assets/...` image refs) carry over unchanged

## Decisions

| Decision | Choice | Why |
|---|---|---|
| Books model | Top-level sections in one Wiki.js instance | Single deploy, single DB/auth; books are conceptual, not infrastructural |
| Folder layout | `<locale>/<book>/<module>/<page>` | Locale stays the outermost axis; matches existing Wiki.js locale toggle behavior |
| Locales | EN + TH for both books | Symmetry with current Inventory layout; `sync_nav` already designed around this pair |
| Entry UX | Global landing (2 cards) + per-book home + shared sidebar showing both books as headers | Wiki.js can render this natively; no JS injection required |
| Platform scope | Structure + skeleton pages (frontmatter, At a Glance outline, References to source repo, TODO checklist) | Lets us validate the two-book structure end-to-end; deep content arrives as follow-up PRs |
| Internal links | Rewrite everything in one pass (script-driven) | Many cross-page links exist; mass rewrite is safer than ad-hoc fixes |
| Migration mechanic | `git mv` + Python script for link/image rewrites | Preserve blame; deterministic mapping |
| Assets | `assets/screenshots/<book>/<module>/<slug>.png` | Namespaces by book; prevents future module-name collisions (e.g., `dashboard` exists in both Inventory and Platform) |

## Architecture overview

### Before

```
carmen-wiki/
├── en/
│   ├── home.md
│   ├── access-control/
│   ├── costing/
│   ├── good-receive-note/
│   └── ... (18 inventory modules)
├── th/ (mirror)
├── assets/screenshots/<module>/
└── scripts/sync_nav/
```

### After

```
carmen-wiki/
├── en/
│   ├── home.md                          # global landing — 2 cards
│   ├── inventory/
│   │   ├── home.md                      # Inventory book index
│   │   ├── access-control/
│   │   ├── costing/
│   │   └── ... (18 modules moved here)
│   └── platform/
│       ├── home.md                      # Platform book index
│       ├── clusters/
│       ├── business-units/
│       ├── users/
│       ├── report-templates/
│       ├── profile/
│       └── auth-roles/                  # cross-cutting role/JWT reference
├── th/                                  # mirrored structure
├── assets/screenshots/
│   ├── inventory/<module>/<slug>.png
│   └── platform/.gitkeep                # empty for now; skeleton has no screenshots
└── scripts/
    ├── sync_nav/                        # extended for per-book nav
    └── migrate_books/                   # one-shot migration tooling
```

### URL changes (Wiki.js)

- `/en/costing/calculation-methods` → `/en/inventory/costing/calculation-methods`
- `/th/costing/calculation-methods` → `/th/inventory/costing/calculation-methods`
- New: `/en/platform/clusters/home`, `/th/platform/clusters/home`

Bookmarks to old URLs will break. Acceptable because the wiki is internal/dev-only and there are no external consumers.

## Landing & navigation

### Global landing (`en/home.md`, `th/home.md`)

- Hero: "Carmen Wiki — internal reference for developers and testers"
- Two side-by-side cards:
  - **Carmen Inventory** — short blurb, link to `/<locale>/inventory/home`
  - **Carmen Platform** — short blurb, link to `/<locale>/platform/home`
- No module-level links on the global landing (keeps scope clear)

### Per-book home (`<locale>/<book>/home.md`)

- Title + 1-paragraph overview (audience + scope of the book)
- Table of modules with one-line descriptions and links
- Frontmatter includes `tags: book/inventory` or `tags: book/platform` to enable future filtering

### Wiki.js sidebar nav

Wiki.js custom navigation tree (driven by `sync_nav`) renders both books simultaneously:

```
📚 Carmen Inventory                     ← header (divider)
   ├── Home              /<locale>/inventory/home
   ├── Access Control    /<locale>/inventory/access-control/home
   ├── Costing           /<locale>/inventory/costing/home
   ├── Good Receive Note ...
   └── ... (18 modules)

📚 Carmen Platform                      ← header (divider)
   ├── Home              /<locale>/platform/home
   ├── Clusters          /<locale>/platform/clusters/home
   ├── Business Units    ...
   ├── Users             ...
   ├── Report Templates  ...
   ├── Profile           ...
   └── Auth & Roles      ...
```

The active item is highlighted by Wiki.js based on current path. Both books always visible — switching books = clicking the other header's home or any module under it.

**Not in scope:** scoped sidebar (hide the other book's modules based on URL path). Would require Wiki.js theme customization or JS injection.

## Internal link rewrite

### Mapping table (generated)

```
/en/<module>/...   →   /en/inventory/<module>/...
/th/<module>/...   →   /th/inventory/<module>/...
/assets/screenshots/<module>/...   →   /assets/screenshots/inventory/<module>/...
```

For each of the 18 existing Inventory modules.

### Patterns rewritten

- Markdown link syntax: `[text](path)` and `[text](path#anchor)`
- Image syntax: `![alt](path)`
- Root-relative paths only (`/en/...`, `/th/...`, `/assets/...`)
- Relative paths within the same module (`./other-page`, `../sibling-module/page`) are left alone — they remain valid after the folder move

### Patterns NOT rewritten

- Code blocks containing path-like strings (parsed as code, not as links)
- External links (`https://`, `http://`)
- Mailto, anchors-only (`#section`)

### Implementation

- Script: `scripts/migrate_books/rewrite_links.py`
- Uses a real markdown parser (e.g., `markdown-it-py`) to avoid raw-text replace mistakes
- Dry-run mode prints every (file, old → new) pair before applying
- After apply, runs verifier: re-scan all `.md` for old paths; non-empty result = fail

## Assets reorganization

- `git mv assets/screenshots/<module> assets/screenshots/inventory/<module>` for each existing Inventory module
- Create `assets/screenshots/platform/.gitkeep` (no platform screenshots yet)
- Image references in markdown are rewritten in the same pass as internal links (Section above)

**Loose `.png` files at the repo root** (e.g., `nav-current.png`, `grn-receiver-edit.png`, ~25 files): out of scope. These appear to be session working files, not assets referenced by any page. Leave untouched.

## sync_nav extension

### Current state

`scripts/sync_nav/` pushes one navigation tree from EN → TH via Wiki.js GraphQL, with labels resolved from page titles + an overrides YAML.

### Required changes

1. **Config schema** — `nav-overrides.yaml` grows a `books:` block:

   ```yaml
   books:
     inventory:
       label_en: "Carmen Inventory"
       label_th: "Carmen Inventory"
       home: /<locale>/inventory/home
       modules:
         - slug: costing
           label_en: "Costing"
           label_th: "การคิดต้นทุน"
         - slug: good-receive-note
           label_en: "Good Receive Note"
           label_th: "ใบรับสินค้า"
         # ... all 18 inventory modules
     platform:
       label_en: "Carmen Platform"
       label_th: "Carmen Platform"
       home: /<locale>/platform/home
       modules:
         - slug: clusters
           label_en: "Clusters"
           label_th: "Clusters"
         # ... all 6 platform modules
   ```

2. **Tree builder** — generate Wiki.js nav tree from the config:
   - Insert a `header` item per book (using `label_<locale>`)
   - Under each header, emit `link` items for the book's home + every module's home page
   - Insert a `divider` between books

3. **Discovery update** — current implementation likely walks `en/<module>/home.md` at locale root. New behavior walks `en/<book>/<module>/home.md` for each book defined in config.

4. **Tests** — extend `scripts/sync_nav/test_sync_nav.py` with:
   - Two-book tree construction
   - Per-book label resolution from frontmatter title vs overrides
   - Mode assertion (dry-run vs push)

### Touch list

- `scripts/sync_nav/nav-overrides.yaml`
- `scripts/sync_nav/sync_nav.py` (and any internal modules — tree, transform, resolve_label)
- `scripts/sync_nav/test_sync_nav.py`
- `scripts/sync_nav/README.md` — document the two-book model

### Unchanged

- GraphQL mutation logic (Wiki.js accepts a nav tree regardless of shape)
- TH-from-EN pairing logic (still per-locale)

## Platform book skeleton

Each Platform module page uses the existing Wiki.js frontmatter + numbered-section convention.

### Page list

```
en/platform/
├── home.md                              # book index
├── clusters/
│   ├── home.md                          # module overview
│   ├── data-model.md                    # Cluster entity + relationships
│   ├── ui-screens.md                    # ClusterManagement, ClusterEdit, BU/user assignments
│   └── permissions.md                   # platform_admin, support_manager, support_staff gates
├── business-units/
│   ├── home.md
│   ├── data-model.md
│   └── ui-screens.md                    # multi-section form, hotel/company info, formats, timezone, DB connection, config array
├── users/
│   ├── home.md
│   ├── data-model.md
│   ├── ui-screens.md                    # role + status filters, per-cluster BU assignments
│   └── lifecycle.md                     # hard/soft delete, password reset
├── report-templates/
│   ├── home.md
│   ├── xml-spec.md                      # Dialog + Content XML structure, Label/Date/Lookup pairs
│   └── ui-screens.md                    # CodeMirror tabs, preview, chip inputs, sticky action bar
├── profile/
│   └── home.md                          # view/edit, change password
└── auth-roles/
    └── home.md                          # JWT + role gates table (5 roles)
```

`th/platform/` mirrors this structure file-for-file.

### Skeleton page content

```yaml
---
title: <Page Title>
description: <one-line summary>
published: true
date: 2026-05-19T00:00:00.000Z
tags: book/platform, <module>
editor: markdown
dateCreated: 2026-05-19T00:00:00.000Z
---
```

Followed by:

- `## 1. At a Glance` — 1–2 sentences + bullet list of intended subtopics
- `## 2. References` — links to source-of-truth files in `../carmen-platform/`:
  - `CLAUDE.md` (page patterns, conventions)
  - `SITEMAP.md` (routes, navigation)
  - `docs/OVERVIEW.md` (product/architecture/entities)
  - `docs/DEVELOPMENT.md` (setup, env, API, auth)
  - Specific `src/pages/<Component>.tsx` paths when relevant
- `## 3. TODO` — bulleted checklist of subsections still to be written

"Skeleton" means: complete frontmatter + the three sections above with real content (references and the TODO list reflect the actual module). Skeleton pages are publishable and useful as navigation anchors and PR references even without deep content.

## Migration mechanics

### Branch + commit strategy

Branch: `feat/multi-book-restructure`

Commits (in this order, all on the branch, all merged in one PR):

1. `scripts(migrate_books): scaffold migration tooling` — empty package + README describing the phases
2. `scripts(migrate_books): folder move generator` — produces the `git mv` plan
3. `chore(inventory): move existing modules under en/inventory and th/inventory` — execute folder moves (git mv) for content + assets
4. `scripts(migrate_books): markdown link/image rewriter` — implement + tests
5. `chore(inventory): rewrite internal links and image refs` — run the rewriter
6. `feat(platform): add Platform book skeleton (EN + TH)` — new platform pages
7. `feat(home): rewrite global landing to two-card layout` — `en/home.md`, `th/home.md`
8. `feat(home): add per-book home pages` — `<locale>/<book>/home.md`
9. `scripts(sync_nav): support per-book navigation` — config schema + tree builder + tests
10. `docs: update CLAUDE.md and MEMORY pointers for multi-book layout` — refresh project memory
11. `scripts(sync_nav): push two-book nav to Wiki.js` — actual nav update (or a script run note in the PR if performed manually)

Each commit reviewable on its own.

### Estimated scope

- ~36 module folder `git mv`s (18 modules × 2 locales)
- 18 asset folder `git mv`s
- ~100–300 markdown link rewrites (exact count from dry-run)
- ~34 new Platform skeleton files + 4 new book-home files (2 books × 2 locales) + 2 rewritten root landing pages
- ~3–5 script files touched + tests

## Verification

### Static checks (before push)

1. `python scripts/migrate_books/verify.py` — re-scans every `.md` for old paths; non-empty result = fail
2. `python .specs/verify_frontmatter.py` — every page has valid Wiki.js frontmatter (already exists)
3. `python -m pytest scripts/sync_nav/test_sync_nav.py` — sync_nav unit tests pass

### sync_nav dry-run

`python -m scripts.sync_nav --dry-run` prints the resolved Wiki.js nav tree. Visual check:

- Two book headers present
- Each header followed by the expected module link list
- Divider between books
- TH variant uses TH labels and `/th/...` paths

### Visual verification in dev Wiki.js

After pushing the branch and letting storage Git editor pull:

- Visit `http://dev.blueledgers.com:3987/`
- Confirm global landing renders two cards
- Click each book → lands on book home page
- Sidebar shows both book headers + module lists
- Open a sample inventory page (e.g., `/en/inventory/costing/calculation-methods`) — page renders, internal links work
- Open a Platform skeleton page (e.g., `/en/platform/clusters/home`) — frontmatter rendered, three sections present
- TH variant (`/th/...`) renders correspondingly

Screenshots from these checks attached to the PR description.

### Rollback

- Pre-merge: `git checkout main; git branch -D feat/multi-book-restructure`
- Post-merge: `git revert <merge-commit>` — Wiki.js storage sync restores previous layout on the next pull
- No data loss risk: all content moves are `git mv`, all rewrites are deterministic

### Known risks

- **Wiki.js cache** may briefly hold old URL entries. If observed, trigger a cache rebuild via Wiki.js admin.
- **Search index** must rebuild after path changes. Verify after merge; rebuild via Wiki.js admin if results are stale.
- **`sync_nav` push** is a side-effecting operation against Wiki.js. The PR should be merged before pushing nav to avoid mismatch between git state and Wiki.js sidebar.

## Out of scope

- Deep content for Platform pages (skeletons only — followed up per-module in separate PRs)
- Additional books beyond Inventory + Platform (micro-report, micro-cronjobs, backend, mobile) — folder layout supports them, but they are not created here
- Wiki.js theme/JS customization (e.g., scoped sidebar per book)
- HTTP 301 redirects from old paths — would need nginx-layer changes outside Wiki.js
- Cleanup of loose `.png` files at repo root
- Changing the documentation engine (mdBook, Docusaurus, etc.)

## Memory and convention updates

The following project-level docs need updates as part of this work:

- `CLAUDE.md` — update folder-structure guidance to reflect `<locale>/<book>/<module>/<page>`
- `.claude/memory/wiki_structure_decisions.md` — record the multi-book decision
- `.claude/memory/screenshot_pattern.md` — update path to `assets/screenshots/<book>/<module>/<slug>.png`
- `scripts/sync_nav/README.md` — document `books:` config block and two-book tree generation
- `.specs/` indexes/templates — update path examples if any reference the old `en/<module>/` layout

## Open follow-ups (post-merge, not blocking this design)

- Author Platform module content (one PR per module, following existing inventory module patterns)
- Decide whether to add a `dashboard` Platform module (currently in `carmen-platform` SITEMAP but not listed in this skeleton)
- Decide whether to add `landing` and `login` pages to the Platform book or treat them as part of `auth-roles`
- Audit and clean up loose root `.png` files
