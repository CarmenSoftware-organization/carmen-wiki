# Screenshots for Every Screen Page, Both Books — Design

**Date:** 2026-09-23
**Status:** Approved in chat (approach A), pending spec review
**Repos touched:** `carmen-wiki`, `carmen-inventory-frontend-e2e`, `carmen-platform-e2e`
**Branch in each repo:** `docs/screenshots-all-books`
**Supersedes the manual remap in:** `2026-06-10-screenshot-full-recapture-design.md`

## 1. Goal

Every wiki page that documents a real application screen shows a current screenshot of that screen, in both the Inventory and Platform books, EN and TH. The capture must be repeatable, so the next UI change is a re-run rather than a manual remap.

### 1.1 Current state (2026-09-23, EN; TH mirrors EN)

| Page type | Inventory | Platform |
|-----------|-----------|----------|
| Module landing | 17/19 | 0/29 |
| Feature / sub-page | 48/73 | 0/29 |
| User-flow, test-scenarios, data-model, business-rules | 0/152 | 0/17 |

Known problem ("two organizations"): the Inventory capture pipeline names output folders after the frontend route, while pages embed images from wiki-taxonomy folders. Refreshing screenshots has required a hand-written `cp` remap every time.

### 1.2 Out of scope

- Page types with no single screen: `user-flow`, `test-scenarios`, `data-model`, `business-rules`, and every `permissions.md`.
- Concept pages with no route: `inventory/costing.md`, `costing/calculation-methods`, `general-ledger/gl-posting`, `system-config/doc-version`, `platform/users/lifecycle`, `platform/report-templates/xml-spec`.
- Per-step screenshots inside user-flow pages.
- Separate TH captures — TH pages embed the same EN-UI image (existing convention).
- New automated tests (per user preference); existing suites and type-checks must still pass.

## 2. Page ↔ Image Convention

No mapping file. The embed step pairs images with pages by path:

| Image on disk | Embedded in |
|---------------|-------------|
| `assets/screenshots/<book>/<module>/index.png` | `<locale>/<book>/<module>.md` (module landing) |
| `assets/screenshots/<book>/<module>/<slug>.png` | `<locale>/<book>/<module>/<slug>.md` |
| `assets/screenshots/<book>/<module>/<slug>-<variant>.png` | same page as `<slug>`, after the base image (e.g. `ui-screens-form.png`, existing `department-detail.png`) |

Platform `ui-screens.md` pages get two images: `ui-screens.png` (list) and `ui-screens-form.png` (create/edit form) where a form route exists.

### 2.1 Wiki.js asset URLs

| Book | Asset Manager folder | Markdown URL |
|------|----------------------|--------------|
| Inventory | `screenshots/<module>/` (unchanged) | `/screenshots/<module>/<file>.png` |
| Platform | `screenshots/platform/<module>/` (new) | `/screenshots/platform/<module>/<file>.png` |

Platform is namespaced because its `dashboard` and `profile` modules would collide with existing Inventory asset folders. Existing Inventory URLs are not changed.

## 3. Page → Route Mapping

The capture manifests carry this mapping. Relative React routes are resolved to full paths from the frontend router during implementation. A page whose candidate route does not render the described screen, or needs a record id that cannot be discovered, is recorded as **skipped with a reason** — never embedded with a wrong image.

### 3.1 Inventory gaps (22 listed, 4 expected skips)

| Wiki page | Candidate route |
|-----------|-----------------|
| `access-control/business-unit-user` | `/system-admin/user/:id` (business-unit section) |
| `access-control/department-user` | `/config/department/:id` (users section) |
| `access-control/permission` | `/system-admin/role/:id` |
| `access-control/user-location` | `/config/location/:id` (users section) |
| `dashboard/my-approval` | `/procurement/approval` |
| `dashboard/my-pending` | `/dashboard` (my-pending widget) |
| `dashboard/widget-workspace` | `/dashboard` |
| `general-ledger` (landing) | `/accounting/journal-voucher` |
| `master-data/chart-of-accounts` | `chart-of-accounts` route |
| `master-data/cost-center` | none found → expected skip |
| `master-data/shelf` | `shelf` route |
| `master-data/vendor-business-type` | `/config/business-type` |
| `reporting-audit/attachment` | none found → expected skip |
| `reporting-audit/notification` | `/notifications` |
| `reporting-audit/report` | `/report` |
| `reporting-audit/widget` | `/system-admin/dashboard-dataset` |
| `system-config/application-config` | `business-setting` / `default-setting` route |
| `system-config/company-profile` | `company-profile` route |
| `system-config/dashboard-dataset` | `/system-admin/dashboard-dataset` |
| `system-config/dimension` | none found → expected skip |
| `system-config/menu` | none found → expected skip |
| `system-config/query-dataset` | `/system-admin/query-dataset` |

Existing embedded Inventory images are also refreshed: every existing shot whose output maps to a curated file gets a `wikiTarget`, so one capture run updates old and new images alike.

### 3.2 Platform (47 pages)

| Wiki page | List / main route | Form route (`ui-screens-form`) |
|-----------|-------------------|--------------------------------|
| `landing` | `/` | — |
| `dashboard` | `/dashboard` | — |
| `changelog` | `/changelog` | — |
| `profile` | `/profile` | — |
| `activity-events` | `/activity-events` | — |
| `usage-analytics` | `/analytics` | — |
| `sql-workbench` | `/sql-workbench` | — |
| `clusters`, `clusters/ui-screens` | `/clusters` | `/clusters/new` |
| `applications`, `applications/ui-screens` | `/applications` | `/applications/new` |
| `business-units`, `business-units/ui-screens` | `/business-units` | `/business-units/new` |
| `business-units/tenant-migrations`, `tenant-migrations` | `/tenant-migrations` | — |
| `tenant-imports`, `tenant-imports/ui-screens` | `/tenant-imports` | — |
| `licenses`, `licenses/ui-screens` | `/licenses` | `/licenses/:clusterId` |
| `license-catalog`, `license-catalog/ui-screens` | `/license-feature-groups` | `/license-feature-groups/new` |
| `users`, `users/ui-screens` | `/users` | `/users/new` |
| `user-platform`, `user-platform/ui-screens` | `/platform/user-platform` | `/platform/user-platform/:userId` |
| `rbac`, `rbac/ui-screens` | `/platform/roles` | `/platform/roles/new` |
| `super-admins` | `/platform/super-admins` | — |
| `report-templates`, `report-templates/ui-screens` | `/report-templates` | `/report-templates/new` |
| `report-form-groups`, `report-templates/form-groups` | `/report-form-groups` | — |
| `news`, `news/ui-screens` | `/news` | `/news/new` |
| `broadcasts`, `broadcasts/ui-screens` | `/broadcasts` | `/broadcasts/new` |
| `cronjobs`, `cronjobs/ui-screens` | `/cronjobs` | `/cronjobs/new` |
| `database-pools`, `database-pools/ui-screens` | `/platform/database-pools` | `/platform/database-pools/new` |
| `cluster-admin`, `cluster-admin/ui-screens` | `/cluster-admin` | `/cluster-admin/:clusterId/business-units` |
| `email-settings` | `/platform/email-settings` | — |
| `platform-config` | `/platform/configs` | — |
| `platform-migrations` | `/platform/migrations` | — |
| `feature-flags` | `/platform/features` | — |

Where two pages share a route, one capture is written to both targets (`wikiTarget` accepts a list).

## 4. Capture Pipelines

### 4.1 Inventory — `carmen-inventory-frontend-e2e`

- `ShotSpec` gains optional `wikiTarget: string | string[]` (`"<module>/<file>"`, no extension). When set, the PNG is written to `<WIKI_ASSETS_DIR>/<wikiTarget>.png` for each target; otherwise behaviour is unchanged (route-derived folder).
- Add shots for §3.1; add `wikiTarget` to existing shots that feed curated images.
- Unchanged capture rules: viewport capture (never `fullPage`), `domcontentloaded` + bounded `networkidle`, wait for skeletons, 60 s hard timeout per spec, seed ids from `discover-seeds.ts`, skip-with-reason recorded in `last-run.json`.
- Capture user: data-rich tenant via `WIKI_CAPTURE_EMAIL`; frontend at `:3000` pointing at a running backend.

### 4.2 Platform — `carmen-platform-e2e`

- New `tests/wiki-screenshots/` with `types.ts`, `manifest.ts` (§3.2) and `capture.spec.ts`, writing `last-run.json`; new Playwright project `wiki-screenshots` and script `wiki:capture`.
- Reuses the repo's existing super-admin auth setup and `.env` handling; no credentials in code.
- Same capture rules as §4.1. Output root `WIKI_ASSETS_DIR` defaults to `../carmen-wiki/assets/screenshots/platform`.
- Dynamic routes (`:clusterId`, `:userId`) take an id from the list API response observed on the list page; unresolvable → skip with reason.

## 5. Embed & Publish — `carmen-wiki`

### 5.1 `scripts/embed_screenshots.py`

- Walks `assets/screenshots/<book>/**/*.png`, resolves each to its page per §2, and inserts `![<page title> screen](<url>)` (variants: `![<page title> <variant> screen](<url>)`) into **both** `en/` and `th/` pages. TH alt text uses the TH page title.
- Placement: one blank line after the `> **At a Glance**` block; if absent, immediately before the first `## 1.` heading; if neither, after the H1.
- Idempotent: an image URL already present in the page is not inserted again. Updates `date` in frontmatter only for pages it changes; never touches `dateCreated`.
- Skips images that resolve to out-of-scope page types (§1.2) or to no page, and lists them.
- `--dry-run` prints the planned inserts per page. The dry-run output is reviewed before a real run, because existing asset folders may hold files that were never meant to be embedded.

### 5.2 Asset upload

`scripts/upload_assets.sh` currently hard-codes 17 Inventory folder ids. It changes to resolve the target folder by path through the Wiki.js GraphQL assets API, creating missing folders (`general-ledger`, `platform`, `platform/<module>`), so it serves both books.

### 5.3 Publish and verify

1. Upload new and refreshed PNGs (§5.2).
2. `push_pages.py` for every changed page, EN and TH.
3. curl every embedded screenshot URL on the dev wiki — all must return 200.
4. Record the final coverage (before → after per book, plus skips with reasons) in the wiki PR body.

## 6. Error Handling

| Situation | Behaviour |
|-----------|-----------|
| Backend down / login fails | Capture aborts loudly (existing CI guard on unexpected skips); no images overwritten |
| Route needs an id that cannot be found | Skip with reason; old image (if any) kept |
| Page hangs past 60 s | Page closed, skip recorded as timeout |
| Image has no matching page | Listed by the embed dry-run, not embedded |
| Upload fails for a file | Reported per file; pages referencing it are not pushed |

## 7. Verification & Done Criteria

- Type-check passes in both e2e repos; the `scripts` test suite in `carmen-wiki` passes.
- Final report: pages with screenshots per book (before → after), and every skipped page with its reason.
- Every embedded URL returns 200 on the dev wiki, in both locales.
- One PR per repo; the wiki PR merges last.
