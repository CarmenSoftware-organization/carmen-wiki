# Platform Book Full Re-sync — Design (2026-09-05)

## Goal

Bring the **Platform book** (`en/platform/`, `th/platform/`) back in line with the
current state of `../carmen-platform`, add pages for every admin surface that has
none, remove the one module whose feature was deleted from the product, rewrite the
coverage checklist against the current SPA, and push the result to the dev Wiki.js
instance.

Last Platform book edit: **2026-07-29** (`docs(resync): new pages — platform/dashboard + platform/landing`).
Source delta since then: **972 commits** in `carmen-platform`.

Heaviest-changed source areas in that window, ranked by **how many times a file under each path appears across the window's commits** — not by commit count. One commit touching three files under a path contributes three. The figures are a relative heat map, nothing more: `src/pages/tenantImport` shows 36 here while only 25 commits touched it. Do not quote these as commit counts.

| Path | File-touch count (not commits — see note) |
|------|--------------------:|
| `src/pages/licenses` | 228 |
| `src/pages/clusterAdmin` | 161 |
| `src/i18n/{en,th}.ts` | 255 |
| `src/pages/businessUnitEdit` | 98 |
| `src/pages/clusterEdit` | 78 |
| `src/types/index.ts` | 68 |
| `src/pages/platformConfig` | 39 |
| `src/pages/tenantImport` | 36 |
| `src/pages/emailSettings` | 36 |

## Approach (chosen)

**Snapshot verification** of every existing page (same method as the 2026-07-15
re-sync). Do not reconstruct changes from git history; verify each page's claims
against the *current* source. Git log is a hint for where to look; the source of
truth for every edit is current code.

Precedence per CLAUDE.md: **implementation + e2e (`../carmen-platform-e2e`) >
`../carmen/docs/` > memory or speculation.**

**Module layout: flat** (approach B of three considered). New modules become
sibling folders under `<locale>/platform/`; no existing folder moves. The SPA's
eight nav groups are expressed on the `platform.md` landing page and in the Wiki.js
nav tree, not in the folder structure — same reading experience, none of the
link-breakage risk of a mid-re-sync folder migration.

## Scope

### Existing pages to verify (13 units)

Eight folder modules — `clusters`, `business-units`, `users`, `rbac`,
`applications`, `broadcasts`, `news`, `report-templates` — plus five standalone
pages: `sql-workbench.md`, `dashboard.md`, `landing.md`, `profile.md`,
`changelog.md`. Roughly 76 pages across both locales.

Known drift to fix (found during design, not exhaustive):

| Module | Change in source |
|--------|------------------|
| `business-units` | User no longer types `code` on create (`#279`); Technical tab has a schema-name randomizer (`#280`); Licenses split out of the Users tab into its own tab (`#276`); New subscription button on the User Licenses card (`#275`) |
| `users` | License content moved out to the new Licenses tab |
| `report-templates` | `template_type` moved into Template Info as a required select (`9cfbf72`); Report Group became a code select in form mode (`9843bb0`); Standard hidden and forced true in form mode (`5734758`); Business Unit Scope read-only and cleared in form mode (`b513dee`); list columns restructured (`4a91abf`); default sort by name A→Z (`a4d994c`) |
| `rbac` | New permission keys across the board; sidebar order now derives from `NAV_RESOURCE_ORDER` in `platformNav.ts` so role permission lists read in menu order; multi-BU role-permission seeding (`#281`) |
| all | i18n plural-inflection fixes changed 32 user-visible English strings |

### Module to remove (1)

`print-template-mapping` — removed from the product by `de11377` (2026-07-24),
`feat(report-template): remove the print template mapping pages`: 1,476 deletions
covering the page components, service, `App.tsx` routes, breadcrumb entry, and the
permission key in `src/utils/permissions.ts`. Nothing in `ReportTemplateEdit.tsx`
or `ReportTemplateManagement.tsx` references mapping any more. The capability was
superseded by the `template_type` field on report templates and by the new Form
Groups surface. The wiki module is therefore deleted in both locales, with a
`changelog.md` entry recording the removal date.

### Modules to create (17)

Grouped by the SPA nav group they belong to (`src/components/nav/platformNav.ts`,
`src/components/nav/clusterAdminNav.ts`):

| Nav group | New module | Routes |
|-----------|-----------|--------|
| Organization | `tenant-migrations` | `/tenant-migrations` |
| Organization | `tenant-imports` | `/tenant-imports` |
| License Management | `licenses` | `/licenses`, `/licenses/:clusterId`, `/licenses/subscriptions/*`, `/licenses/seats/*`, `/licenses/bu-quota/*`, `/subscriptions/*` |
| License Management | `license-feature-groups` | `/license-feature-groups`, `/license-feature-groups/:id/edit`, `/license-feature-groups/new` |
| License Management | `license-features` | `/license-features` |
| Content | `report-form-groups` | `/report-form-groups` |
| Analytics | `usage-analytics` | `/analytics` |
| Analytics | `activity-events` | `/activity-events` |
| Scheduling | `cronjobs` | `/cronjobs`, `/cronjobs/:id/edit`, `/cronjobs/new` |
| Platform | `platform-config` | `/platform/configs` |
| Platform | `email-settings` | `/platform/email-settings` |
| Platform | `user-platform` | `/platform/user-platform`, `/platform/user-platform/:userId` |
| Platform | `super-admins` | `/platform/super-admins` |
| Platform | `feature-flags` | `/platform/features` |
| Database | `platform-migrations` | `/platform/migrations` |
| Database | `database-pools` | `/platform/database-pools`, `/platform/database-pools/:id/edit`, `/platform/database-pools/new` |
| (second persona) | `cluster-admin` | `/cluster-admin/:clusterId/{cluster,business-units,licenses,users,profile}` |

`cluster-admin` documents a **second navigation and persona**, not a duplicate of
the platform-side modules: it is reached through `ClusterAdminRoute`, every path
carries the cluster id so the sidebar cannot navigate out of its cluster, and it
applies **no permission filtering** (clearing the route guard is the whole check).
Its feature keys are separate from the platform ones with the same menu labels
(`cluster_admin_cluster`, `cluster_admin_business_units`, `cluster_admin_licenses`,
`cluster_admin_users`).

`/platform/category-permissions`, which has no nav entry of its own, is documented
inside the `rbac` module rather than as a module of its own.

### Sub-page depth rule

A new module gets sub-pages only where there is real content, rather than a fixed
four per module:

- **landing** — always.
- **data-model** — when the module owns tables of its own.
- **ui-screens** — when the module has more than one screen.
- **permissions** — when the module has more than one permission key, or has
  `superAdminOnly` / feature-flag gating worth a table.

Rationale: a fixed four-page shape would give `cronjobs` and `super-admins` a
permissions page with a single row, which is the stub outcome the "no stubs" rule
exists to prevent. Estimated result: ~75–90 new pages across both locales rather
than the ~136 a fixed four-page shape would produce.

Every module landing page — new or existing — must state the module's **permission
key**, **feature-flag key**, and whether it is `superAdminOnly`, read from
`platformNav.ts` / `clusterAdminNav.ts`. Menus in this SPA are gated three
different ways and a page written as though every reader sees the menu is wrong.

## Phases

Work branch: `docs/resync-platform-2026-09-05`.
Tracking log: `.specs/resync-platform-2026-09-05-progress.md` — one row per module
recording pages verified, claims fixed, new pages written, e2e backing present or
absent, and routes whose UI changed. The log must carry enough state for a fresh
session to resume at the next row without re-reading earlier work.

### Phase 0 — Source map

Build a per-module table: route in `src/App.tsx` → page component in `src/pages/`
→ service in `src/services/` → permission key in `src/utils/permissions.ts` →
feature key in the nav files → e2e spec in `../carmen-platform-e2e/tests/`.

This table is the input to every later phase and is what flags modules with **no
e2e coverage**, whose behavioral claims must be sourced from implementation alone
and marked as such in the tracking log.

### Phase 1 — Verify the 13 existing units (snapshot)

Per module, in order:

1. Read the current source for the module (page components first, then services,
   types, and e2e as claims require).
2. For each EN page, verify every checkable claim: route paths, field and button
   names, status flows, permission keys, API request/response shapes, edge-case
   tables. Fix inline.
3. Frontmatter: bump `date` to now. **Never touch `dateCreated`** — corrupting it
   is a known failure from a previous re-sync.
4. Mirror fixes to the TH page semantically; no full re-translation. Because this
   is snapshot mode, also scan the TH page for drift of its own against the EN
   structure.
5. Flag visually-changed routes in the tracking log for the deferred screenshot
   round.
6. Run `.specs/verify_frontmatter.py`; commit per module.

### Phase 2 — Remove `print-template-mapping`

Delete the module folder in both locales; remove its card from `platform.md` and
any §7 sub-page links pointing at it; add a `changelog.md` entry recording removal
from the product on 2026-07-24; drop it from `scripts/nav-overrides.yaml` so the
Phase 5 nav rebuild does not resurrect it.

### Phase 3 — Create the 17 new modules

Order (highest reader impact first): licenses group (3) → `cluster-admin` (1) →
platform group (5) → organization (2) → analytics (2) → database (2) →
`cronjobs` (1) → `report-form-groups` (1) — 17 modules total.

Scaffold with the existing tool rather than by hand:

```
python3 scripts/migrate_books/scaffold_platform.py \
  --config scripts/migrate_books/platform_pages.yaml \
  --today "<current ISO timestamp>"
```

It writes EN and TH in one pass with correct Wiki.js frontmatter and skips existing
files unless `--force` is given. **Pass `--today` explicitly** — the default is a
hard-coded `2026-05-19T00:00:00.000Z`, which would stamp every new page with a
four-month-old creation date. Add the new modules' page specs to
`platform_pages.yaml` first; that file, not ad-hoc file creation, is the record of
what the book contains.

Then fill each scaffold from source: EN first, TH after. §7 sub-page lists use
absolute-URL markdown links (`[Display](/en/platform/<module>/<slug>)`) — pipe
wikilinks do not render in this Wiki.js. Add each new module's card to the correct
nav-group section of `platform.md`.

### Phase 4 — Coverage checklist

Rewrite `.specs/platform-coverage-checklist.md` against the current SPA: enumerate
sub-processes for every unit the book holds after this re-sync — 25 folder modules
(8 kept + 17 new) and 5 standalone pages — and replace the "as of 2026-06-11" summary whose
100% figure is measured against a June snapshot of the SPA and is therefore
misleading today. Record the `carmen-platform` HEAD commit the new count is
measured against.

### Phase 5 — Dev Wiki.js sync

1. Update the `books:` block in `scripts/nav-overrides.yaml` (17 additions, 1
   removal, `label_th:` for every new entry).
2. `push_pages.py` for changed and new pages only.
3. `sync_nav.py --mode=build --dry-run`, read every line, then apply. Build mode is
   required because the change is structural, and it rebuilds the whole tree from
   the YAML — so the YAML must be correct before it runs.
4. Spot-check rendering on `http://dev.blueledgers.com:3987/` for one page per nav
   group, in both locales.

## Error handling

- Wiki claim not found anywhere in source → rewrite from current source; note the
  discrepancy in the tracking log.
- Ambiguous behavior → e2e and implementation win over `../carmen/docs/`.
- Module with no e2e coverage → source claims from implementation, mark
  "no e2e backing" in the tracking log, do not invent behavior.
- Wiki.js push failure → per-page retry, then log and continue.
- `sync_nav.py` dry-run diff that does not match intent → stop, fix
  `nav-overrides.yaml`, re-run. Never apply build mode on an unread diff.

## Verification (definition of done)

1. `.specs/verify_frontmatter.py` passes on every touched page, and no existing
   page's `dateCreated` changed (checked with `git diff`).
2. Every internal `/en/platform/…` and `/th/platform/…` link resolves to a page
   that exists; no link to `print-template-mapping` remains.
3. EN and TH page counts match per module.
4. Two-way nav check: every entry in `platformNav.ts` and `clusterAdminNav.ts` has
   a wiki module, and every wiki module has a backing route.
5. Coverage checklist numbers match actual page state and name the source HEAD.
6. One page per nav group renders correctly on dev Wiki.js in both locales.
7. Work lands as a PR from `docs/resync-platform-2026-09-05`.

## Out of scope

- **Screenshots** — deferred to a separate round by decision. Platform has no
  screenshot pipeline at all today: `assets/screenshots/platform/` is empty,
  `carmen-platform-e2e/package.json` has no `wiki:*` targets, and the `folder_id()`
  map in `scripts/upload_assets.sh` covers only the 17 Inventory modules (ids
  8–24). That round must add a wiki-screenshot Playwright project to
  `carmen-platform-e2e`, create the platform folders in the Wiki.js Asset Manager
  and add their ids to `upload_assets.sh`, then capture the routes this re-sync
  flags as visually changed. It needs a live backend, a data-rich tenant, and a
  cleared `.auth` cache.
- The Inventory book.
- Moving or restructuring existing folders.
- Deferrals recorded in project memory, which stay deferred.

## Follow-up work created by this design

1. Platform screenshot round (above).
2. `scripts/upload_assets.sh` `folder_id()` needs platform entries regardless of
   when screenshots happen.
