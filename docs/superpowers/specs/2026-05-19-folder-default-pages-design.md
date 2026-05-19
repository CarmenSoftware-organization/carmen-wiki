# Folder Default Pages — Standardize on `index.md` + Upgrade Platform Stubs

**Date:** 2026-05-19
**Status:** Approved (awaiting spec review)
**Scope:** all `home.md` files in `en/`, `th/`, plus `scripts/sync_nav.py`, `scripts/nav-overrides.yaml`, `README.md`, and one stray reference in `en/platform/clusters/permissions.md`

## Goal

Standardize the per-folder default landing page across the wiki on a single filename, `index.md`, at every level — language root, book level, and module level. As a second concern, upgrade the six Platform module landing pages from skeleton stubs to the same shape as Inventory module landing pages, in both EN and TH locales.

## Why

Today the wiki has two filename conventions for the per-folder landing page:

- **Inventory module level** uses `index.md` (18 modules × 2 locales = 36 files with rich content).
- **Everywhere else** uses `home.md`: language root (`en/home.md`, `th/home.md`), book level (`en/inventory/home.md`, `en/platform/home.md`, and TH equivalents), and Platform module level (6 × 2 = 12 stub files).

The asymmetry is load-bearing: the book home pages (`en/inventory/home.md` et al.) link to module landings with URL suffix `/home`, but the actual Inventory module files are `index.md`. So the Inventory book home page already has ~36 broken module links in the rendered wiki today.

Standardizing on a single filename eliminates the broken-link footprint and removes a "which convention does this folder use?" question every time someone adds a new page. `index.md` is chosen because the Inventory book — which holds the bulk of the wiki's content (18 modules vs. Platform's 6) and has the most internal cross-links — already uses it. Standardizing on `home.md` would force renaming 36 Inventory files and rewriting ~50 internal back-links in Inventory sub-pages; standardizing on `index.md` renames only the 18 non-Inventory files plus updates the URLs that point at them.

The Platform stub upgrade is bundled because the rename will surface the Platform landing pages in the same navigation slot as the now-consistent Inventory landings, and side-by-side scrutiny will make the stub state stand out.

## Non-goals

- Reviewing or rewriting any existing Inventory `index.md` content. Those pages are already in the canonical shape.
- Updating historical references inside `docs/superpowers/plans/*.md` and `docs/superpowers/specs/*.md`. These are snapshots of past work and should not be retconned.
- Adding new sub-pages or new modules. The 6 Platform modules each get their landing page upgraded; their existing sub-pages are not edited as part of this work.
- Changing Wiki.js infrastructure beyond the one "Default Path" admin setting documented below.

## Constraints

- **Wiki.js navigation script (`scripts/sync_nav.py`) is global.** Renaming a single module's `home.md` would break the script mid-run because line 102 has `HOME_MD = "home.md"` and lines 397–398 read `repo_root / "en" / "home.md"` directly. The script must be updated in lockstep with the renames — a partial rename leaves the repo in a broken state.
- **`scripts/nav-overrides.yaml` carries `home_slug: home`** under each book entry. Wiki.js uses this slug to construct the navigation link URL (`/en/inventory/<home_slug>`), so when files rename to `index.md` the slug must rename to `index` or the sidebar will 404.
- **Wiki.js admin "Default Path" setting** at `dev.blueledgers.com:3987` may be hardcoded to `/en/home`. This setting controls what loads when a user visits `/`. It is configured through the admin UI, not this repo, and must be updated by hand once renames are deployed.
- **Existing internal `[[wiki-style]]` links use module names without `home`/`index` suffix** (e.g. `[[costing/calculation-methods]]`), so they need no change. The vulnerable references are the explicit URL-style links (`/<book>/<module>/home`) inside book and language-root home pages.
- **CLAUDE.md mentions "the repo root `home.md` is a two-card landing"** — but the actual two-card landings live at `en/home.md` and `th/home.md`; no `home.md` exists at the repo root. CLAUDE.md needs a small correction as part of this work.

## Decisions

| Decision | Choice | Why |
|---|---|---|
| Filename | `index.md` at every level | Matches the bulk of existing content (36 Inventory files) and the bulk of existing back-links (~50 `./index` references). Smallest rewrite. |
| Levels covered | Language root + book + module | Half-standardizing (e.g. only module level) would leave the same "which name does this level use?" question one rung up. |
| Wiki.js URL slug | `index` (matching the filename) | Slug and filename are coupled through Wiki.js routing; diverging them is a footgun. |
| Platform content upgrade | Full Inventory template, per-module flexibility allowed | The template is the canonical shape; sections that genuinely don't apply to a Platform module (e.g. regulatory Business Context for `profile`) can be terse or omitted. |
| TH parity | TH renames and content upgrades happen in the same commit as EN | The wiki is bilingual; shipping EN-only would leave TH navigation broken (TH book home pages also link `/home`). |
| Approach | Approach B — module-by-module for content, with one preceding atomic structural commit | The structural rename can't be subdivided without breaking the script mid-stream; content work is naturally per-module. |
| Old plans/specs | Not updated | These are historical records of completed work, not living documentation. |

## Unit decomposition

Seven commits in sequence:

### Unit 0 — Structural rename (atomic)

One commit. Brings the entire repo to a consistent `index.md` baseline. After this unit lands, Wiki.js still works, every existing link resolves, and the only remaining work is Platform content upgrades.

**File renames (18):**

| Level | Files |
|---|---|
| Language root | `en/home.md`, `th/home.md` |
| Book level | `en/inventory/home.md`, `en/platform/home.md`, `th/inventory/home.md`, `th/platform/home.md` |
| Platform modules (EN) | `en/platform/{auth-roles,business-units,clusters,profile,report-templates,users}/home.md` |
| Platform modules (TH) | `th/platform/{auth-roles,business-units,clusters,profile,report-templates,users}/home.md` |

All renames use `git mv` to preserve file history.

**URL updates inside the renamed files:**

| File | Pattern | Approximate count |
|---|---|---|
| `en/index.md` (was `en/home.md`) | `/en/inventory/home` → `/en/inventory/index`, `/en/platform/home` → `/en/platform/index` | 2 URLs |
| `th/index.md` | same | 2 URLs |
| `en/inventory/index.md` | `/en/inventory/<module>/home` → `/en/inventory/<module>/index` | ~18 URLs |
| `en/platform/index.md` | `/en/platform/<module>/home` → `/en/platform/<module>/index` | ~6 URLs |
| `th/inventory/index.md` | same as EN counterpart | ~18 URLs |
| `th/platform/index.md` | same as EN counterpart | ~6 URLs |

**Other updates in U0:**

- `scripts/sync_nav.py` — change `HOME_MD = "home.md"` to `INDEX_MD = "index.md"` (or generalize; whichever the implementation plan prefers) and update ~9 hardcoded path references. Tests in `scripts/test_sync_nav.py` updated alongside.
- `scripts/nav-overrides.yaml` — change `home_slug: home` to `home_slug: index` for both `inventory` and `platform` books. If a name change for the key itself is preferred (e.g. `landing_slug`), the implementation plan should decide.
- `README.md` line 10 — `landing at /en/home` → `landing at /en/index`.
- `en/platform/clusters/permissions.md` and `th/platform/clusters/permissions.md` — both have a `home.md` text reference on line 26 (`Cross-link to auth-roles/home.md`). Update both → `index.md`.
- `CLAUDE.md` — small correction: "the two `en/home.md` / `th/home.md`" instead of "repo root `home.md`". Also update the example frontmatter file path if needed.

**Out of U0 scope:**

- `docs/superpowers/plans/2026-05-18-th-navigation-sync.md`, `2026-05-19-nav-groups.md`, `2026-05-19-multi-book-restructure.md` — references to `/en/home`, `/th/home` preserved as historical snapshots.
- `docs/superpowers/specs/2026-05-18-th-navigation-design.md` — same.

**Verification:**

1. `pytest scripts/` passes (sync_nav tests must be updated to match new filename).
2. `python scripts/sync_nav.py --mode=build --dry-run` (or whatever the script's no-op verification mode is) runs without error.
3. Manually `grep -r "/home)" en th` shows zero hits in current-content files (matches in `docs/superpowers/` are expected).
4. Manually `grep -r "home\.md" scripts/` shows zero hits.
5. Push to `dev.blueledgers.com:3987` and open in browser:
   - `/en/index` loads Carmen Wiki two-card landing
   - `/en/inventory/index` loads Inventory book home
   - `/en/inventory/costing/index` loads Costing module home (unchanged content; only the URL path is checked)
   - `/en/platform/clusters/index` loads Clusters stub (still a stub at this point — that's expected)
   - Click through the book home page to a module — link must resolve, not 404
   - Repeat spot checks for `/th/...`
6. Wiki.js admin → Site Settings → "Default Path" → confirm or update to `/en/index`. This is a manual step and must be checked off explicitly during U0 deployment.

### Units 1–6 — Platform module content upgrades

One commit per Platform module, EN + TH together. Each commit covers: a full rewrite of the module's `index.md` (no longer a stub) and a TH translation that matches.

Sequenced light → heavy so the early units calibrate the template and the heavy ones benefit from that calibration:

| Unit | Module | Sub-pages | Notes |
|---|---|---|---|
| U1 | `profile` | 0 (single file) | Section 4 (Roles) collapses to prose — one role, the signed-in user themselves. Section 7 (Pages in This Module) may state "This module is a single page; see the parent Platform book index." |
| U2 | `auth-roles` | 0 | Section 2 (Business Context) mentions security/access model briefly. |
| U3 | `report-templates` | 2 | Full template. |
| U4 | `business-units` | 2 | Full template. |
| U5 | `clusters` | 3 | Full template — clusters has the richest data model among Platform modules. |
| U6 | `users` | 3 | Full template. |

**Per-module decisions** are made when each unit is implemented, by reading the relevant source under `../carmen-platform/` (SITEMAP + the named React page files in `src/pages/`). The template structure is fixed (see next section); the per-module judgment is which sections need terse treatment versus full prose, what to put in "Related Modules" (e.g. clusters relates to business-units, users relates to auth-roles), and how to phrase the At a Glance entry.

**Verification (per unit):**

1. Open `dev.blueledgers.com:3987/en/platform/<module>/index` in browser — full content renders, no stub TODO markers remain, every cross-link resolves.
2. Switch language toggle to TH — `/th/platform/<module>/index` renders the Thai translation in the same shape, no leftover English prose.
3. Sidebar still shows the module under the Platform book at the correct position.
4. `pytest scripts/` still passes (these units don't touch the script, but a regression check is cheap).

## `index.md` template (canonical)

This is the shape every module landing page targets. The Inventory book is already at this shape; Platform modules adopt it through Units 1–6.

**Frontmatter:**

```yaml
---
title: <Module name>
description: <one-line summary used by Wiki.js search and previews>
published: true
date: <ISO 8601 timestamp of last edit>
tags: <book>/<module>, carmen-software
editor: markdown
dateCreated: <ISO 8601 — never change after creation>
---
```

**Body skeleton:**

```markdown
# <Module name>

> **At a Glance**
> **Module purpose:** ... &nbsp;·&nbsp; **Audience:** ... &nbsp;·&nbsp; **Key entities/tables:** ... &nbsp;·&nbsp; **Sub-pages:** N

## 1. Overview
(2–3 paragraphs orienting the reader to what the module does and where it fits in the product)

## 2. Business Context
(1–2 paragraphs on why this module exists, regulatory/operational drivers if any. Terse or omitted when no business angle applies — e.g. `profile`.)

## 3. Key Concepts
(bulleted list of 4–8 terms, each with the term in **bold** and a one-sentence definition)

## 4. Roles and Personas
(table of role | responsibility. Collapses to a sentence of prose when only one role applies.)

## 5. Related Modules
(cross-module flow as a bullet list of `[[other-module]] — relationship` items; followed by master-config dependencies if applicable)

## 6. Reference Sources
(repo paths: concepts, frontend, backend, API contracts, E2E tests — only the ones that actually exist for this module)

## 7. Pages in This Module
(link list to sub-pages with one-line descriptions. For single-page modules, link to the parent book index or note that this module has no sub-pages.)
```

**Per-Platform-module flexibility — applied to Units 1–6:**

Sections are kept but allowed to be terse — they are not removed. Keeping all seven headings preserves the numbered hierarchy (`## 1.` through `## 7.`) so cross-references and reader expectations stay stable across modules.

- Section 2 (Business Context) may be reduced to one or two sentences when the module has no external business driver. Internal admin tools (`profile`, sometimes `auth-roles`) typically qualify. Still present as `## 2. Business Context` with at least one sentence.
- Section 4 (Roles and Personas) collapses to a single line of prose when only one role uses the module (e.g. "Used by the signed-in user themselves.") rather than a one-row table.
- Section 6 (Reference Sources) — Platform modules typically cite only `../carmen-platform/SITEMAP.md` and the specific `src/pages/<Page>.tsx` files; backend / API contracts / E2E lines may be absent when the corresponding source does not exist for the module.
- Section 7 (Pages in This Module) — for single-file modules (`profile`, `auth-roles`), state explicitly "This module is a single page; see the parent Platform book index" rather than leaving an empty list.

## Risks and open items

| Risk | Mitigation |
|---|---|
| Wiki.js admin "Default Path" setting still points to `/en/home` after U0 deploy → visitors to `/` get a 404 | U0 verification checklist includes the manual admin-UI step. Implementation plan must surface this clearly. |
| Wiki.js page cache serves stale `/en/inventory/home` URL until TTL expires | Acceptable — admin can manually flush page cache, or wait. Document in U0 deployment notes. |
| Mirror-mode `sync_nav.py` invocations elsewhere (CI?) fail because they still pass `--home-file=home.md` or similar | Check `scripts/sync_nav.py` argparse for relevant flags during U0; if any default is `home.md`-flavored, update it. |
| TH translation drift — Platform TH stubs are currently English text under a TH-frontmatter file, not real Thai | Each Platform unit (U1–U6) translates fresh from upgraded EN; do not preserve the current placeholder Thai content. |
| Single-page modules (`profile`, `auth-roles`) feel padded under the full 7-section template | Per-module flexibility documented above — allow Section 2 and Section 4 to be terse or absent. |

## Out of scope (explicit)

- Renaming of `index.md` files inside Inventory modules (already at target state).
- Sub-page back-link updates inside Inventory modules (still `./index`, still correct).
- Adding new modules to either book.
- Changing the `tags` taxonomy beyond what the template specifies.
- Updating any file under `docs/superpowers/plans/` or `docs/superpowers/specs/` to reflect the new URL convention.
- Wiki.js theme, plugin, or storage backend changes.
