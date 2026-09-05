# Carmen Platform — Process Coverage Checklist

Internal tracker (not a published Wiki.js page). Enumerates every Carmen Platform
admin-SPA process by module — sourced from the **carmen-platform SPA source**
(`src/App.tsx`, `src/pages/`, `src/services/`) and the **Prisma platform schema** —
and records whether the wiki documents it. Answers: "is the Platform documentation
project finished?". Sibling of `.specs/process-coverage-checklist.md` (Inventory book);
kept separate because the two books use different page structures and sources of truth.

How to read: each row is a sub-process. **DM/UI/PERM** = covered in the module's
`data-model` / `ui-screens` / `permissions` page(s); content on the module landing
counts toward whichever axis it serves. Symbols: ✅ complete · 🟡 partial/stub · ⬜ missing.
Tracks the **EN locale** (canonical); TH state is summarized in "Locale coverage".

## Summary (as of 2026-06-11; Shell & Dashboard closed 2026-07-29; Print Template Mapping row removed 2026-09-05 — see Maintenance notes)

| Module | Sub-processes | Done | Partial | Not yet | % complete |
|--------|--------------:|-----:|--------:|--------:|-----------:|
| Clusters | 9 | 9 | 0 | 0 | 100% |
| Business Units | 10 | 10 | 0 | 0 | 100% |
| Users | 10 | 10 | 0 | 0 | 100% |
| Platform RBAC | 8 | 8 | 0 | 0 | 100% |
| Applications | 7 | 7 | 0 | 0 | 100% |
| News | 9 | 9 | 0 | 0 | 100% |
| Broadcasts | 8 | 8 | 0 | 0 | 100% |
| Report Templates | 9 | 9 | 0 | 0 | 100% |
| Profile | 3 | 3 | 0 | 0 | 100% |
| Changelog | 3 | 3 | 0 | 0 | 100% |
| Shell & Dashboard | 2 | 2 | 0 | 0 | 100% |
| **Project total** | 78 | 78 | 0 | 0 | **100%** |

*Print Template Mapping's row (8 sub-processes, 8 done) was removed 2026-09-05 —
the module was deleted from the product 2026-07-24 (`de11377`) and its wiki page
was deleted the same day in this plan's Task 11. The 86→78 total reflects that
subtraction, not new documentation loss; see Maintenance notes.*

## How status is judged

- **DM / UI / PERM cell:** `✅` usable section exists · `🟡` mentioned but incomplete/stub · `⬜` not found · `—` axis not applicable (no SPA surface / no data persistence).
- **Overall row Status:** `✅ Done` all applicable cells ✅ · `🟡 Partial` some but not all ✅ · `⬜ Not yet` all applicable cells ⬜.
- Sub-processes are derived from the SPA at carmen-platform HEAD 2026-06-10 (`f9e4a22` + same-day `<Can>`-gating commits `239b4a9`/`f3f77cf`). New SPA features add rows here.

## Source mapping

| Wiki module | SPA pages | Services / other sources |
|-------------|-----------|--------------------------|
| clusters | ClusterManagement, ClusterEdit | clusterService; Prisma `tb_cluster`, `tb_cluster_user` |
| business-units | BusinessUnitManagement, BusinessUnitEdit | businessUnitService; Prisma `tb_business_unit` (+`_tb_module` join) |
| users | UserManagement, UserEdit | userService; AuthContext; Prisma `tb_user`, `tb_user_profile` |
| rbac | RoleManagement, RoleEdit, PermissionCatalog, SuperAdminManagement, UserPlatformManagement, UserPlatformEdit | role/permission/superAdmin/userRole services; utils/permissions.ts; Prisma `tb_platform_*` |
| applications | ApplicationManagement, ApplicationEdit | applicationService, utils/apiCatalog.ts; backend AppIdGuard + allowlist; Prisma `tb_application`, `tb_application_api` |
| ~~print-template-mapping~~ | *removed 2026-07-24 (`de11377`)* | superseded by `template_type`/`is_default` on `tb_report_template` (migration `20260723120000_print_form_default`) plus the Report Templates → Form Groups sub-page; see Maintenance notes |
| news | NewsManagement, NewsEdit | newsService; backend-gateway news module + micro-cluster; Prisma `tb_news` |
| broadcasts | BroadcastCompose | broadcastService; backend-gateway + micro-notification; Prisma `tb_broadcast_notification`, `tb_user_broadcast_action` |
| report-templates | ReportTemplateManagement, ReportTemplateEdit | reportTemplateService; micro-report; Prisma `tb_report_template` |
| profile | Profile | shared axios (no service file) |
| changelog | Changelog (public) | src/data/changelog.json; build:bump |
| dashboard | Dashboard | six-domain activity/counts services (`clusterService`, `businessUnitService`, `userService`, `applicationService`, `newsService`, `reportTemplateService`) |
| landing | Landing | `VersionBadge`; no service of its own |
| *(undocumented)* | Login | — (screen itself has no dedicated page; its redirect/gate mechanics are covered in RBAC + Users lifecycle) |

## Table A — Modules with full sub-page sets

### 1. Clusters

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | List: search / status filter / show-deleted / CSV | ✅ | ✅ | ✅ | ✅ Done | [UI §2](/en/platform/clusters/ui-screens) |
| 2 | Create cluster (+ post-create nav quirk) | ✅ | ✅ | ✅ | ✅ Done | [UI §3](/en/platform/clusters/ui-screens) |
| 3 | View / edit (Edit-toggle `<Can>`) | ✅ | ✅ | ✅ | ✅ Done | [UI §4](/en/platform/clusters/ui-screens) |
| 4 | Soft delete + Deleted badge | ✅ | ✅ | ✅ | ✅ Done | [UI §2](/en/platform/clusters/ui-screens) |
| 5 | Branding: logo + avatar upload (tokens → presigned) | ✅ | ✅ | ✅ | ✅ Done | [UI §4.2](/en/platform/clusters/ui-screens) |
| 6 | License caps (`max_license_bu`, per-BU user caps) | ✅ | ✅ | — | ✅ Done | [Landing §2](/en/platform/clusters) |
| 7 | Cluster users: add / edit / remove (ungated in-page) | ✅ | ✅ | ✅ | ✅ Done | [PERM §7](/en/platform/clusters/permissions) |
| 8 | Add BU from cluster page (`?cluster_id=` preselect) | — | ✅ | ✅ | ✅ Done | [Landing §1](/en/platform/clusters) |
| 9 | Audit columns (flat-wins, nested fallback) | ✅ | ✅ | — | ✅ Done | [DM §5](/en/platform/clusters/data-model) |

### 2. Business Units

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | List: filters / CSV / logo thumbnail | ✅ | ✅ | ✅ | ✅ Done | [UI §2](/en/platform/business-units/ui-screens) |
| 2 | Create BU + license check flow | ✅ | ✅ | ✅ | ✅ Done | [UI §3](/en/platform/business-units/ui-screens) |
| 3 | Edit (34-field form, 9 sections) | ✅ | ✅ | ✅ | ✅ Done | [UI §4](/en/platform/business-units/ui-screens) |
| 4 | Branding: logo + avatar upload | ✅ | ✅ | ✅ | ✅ Done | [UI §4.10](/en/platform/business-units/ui-screens) |
| 5 | Config entries (key/label/type/value; filter rule) | ✅ | ✅ | — | ✅ Done | [UI §4.8](/en/platform/business-units/ui-screens) |
| 6 | BU users card (add/search/remove) | ✅ | ✅ | ✅ | ✅ Done | [UI §5](/en/platform/business-units/ui-screens) |
| 7 | Soft delete | ✅ | ✅ | ✅ | ✅ Done | [UI §2](/en/platform/business-units/ui-screens) |
| 8 | Audit columns | ✅ | ✅ | — | ✅ Done | [DM §6](/en/platform/business-units/data-model) |
| 9 | Module activation join (`tb_business_unit_tb_module`) — schema-only, no SPA surface | ✅ | — | — | ✅ Done | [DM §2](/en/platform/business-units/data-model) |
| 10 | `cluster.*` key-reuse gotcha (no `business_unit.*` keys) | — | — | ✅ | ✅ Done | [Landing §4](/en/platform/business-units) |

### 3. Users

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | List: avatar / name composition / filters / CSV / audit | ✅ | ✅ | ✅ | ✅ Done | [UI §2](/en/platform/users/ui-screens) |
| 2 | Create user (7 fields; post-create stays in edit mode) | ✅ | ✅ | ✅ | ✅ Done | [Lifecycle §3](/en/platform/users/lifecycle) |
| 3 | Edit user (Edit-toggle `<Can>`; header avatar) | ✅ | ✅ | ✅ | ✅ Done | [UI §4](/en/platform/users/ui-screens) |
| 4 | Admin password reset (`/reset-password`) | ✅ | ✅ | ✅ | ✅ Done | [Lifecycle §5](/en/platform/users/lifecycle) |
| 5 | Keycloak sync (`/fetch-user`) | ✅ | ✅ | — | ✅ Done | [Lifecycle §6](/en/platform/users/lifecycle) |
| 6 | Cluster memberships (read-only card) | ✅ | ✅ | — | ✅ Done | [Landing §2](/en/platform/users) |
| 7 | BU assignments add / remove (cluster-scoped pool) | ✅ | ✅ | ✅ | ✅ Done | [UI §5](/en/platform/users/ui-screens) |
| 8 | Soft delete + hard delete | ✅ | ✅ | ✅ | ✅ Done | [UI §2.4](/en/platform/users/ui-screens) |
| 9 | Login gate (effective permissions / bootstrap) | ✅ | — | ✅ | ✅ Done | [Lifecycle §4](/en/platform/users/lifecycle) |
| 10 | Audit columns + Deleted badge | ✅ | ✅ | — | ✅ Done | [UI §2.5](/en/platform/users/ui-screens) |

### 4. Platform RBAC

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | Permission catalog browse (resource-grouped) | ✅ | ✅ | ✅ | ✅ Done | [UI §3](/en/platform/rbac/ui-screens) |
| 2 | Role create / edit (PermissionPicker, delta writes) | ✅ | ✅ | ✅ | ✅ Done | [DM §2](/en/platform/rbac/data-model) |
| 3 | Role delete (client-ungated — Roles list exception) | ✅ | ✅ | ✅ | ✅ Done | [PERM §2](/en/platform/rbac/permissions) |
| 4 | User role assignment + scope (platform/cluster) | ✅ | ✅ | ✅ | ✅ Done | [UI §5](/en/platform/rbac/ui-screens) |
| 5 | Super admins add / remove (bypass flag) | ✅ | ✅ | ✅ | ✅ Done | [UI §4](/en/platform/rbac/ui-screens) |
| 6 | Effective permissions + `checkPermission` resolution | ✅ | — | ✅ | ✅ Done | [PERM §4](/en/platform/rbac/permissions) |
| 7 | Bootstrap exception (user count ≤ 1) | ✅ | — | ✅ | ✅ Done | [PERM §5](/en/platform/rbac/permissions) |
| 8 | Gate composition (route / sidebar / `<Can>`) incl. legacy migration | — | — | ✅ | ✅ Done | [Landing §5](/en/platform/rbac) |

### 5. Applications

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | List: search / status filter / CSV / App ID column | ✅ | ✅ | ✅ | ✅ Done | [UI §2](/en/platform/applications/ui-screens) |
| 2 | Create application | ✅ | ✅ | ✅ | ✅ Done | [UI §3](/en/platform/applications/ui-screens) |
| 3 | Edit + grouped api_names accordion selector | ✅ | ✅ | ✅ | ✅ Done | [UI §3.4](/en/platform/applications/ui-screens) |
| 4 | `allow_all` vs explicit list (replace semantics) | ✅ | ✅ | ✅ | ✅ Done | [DM §5](/en/platform/applications/data-model) |
| 5 | Catalog generation + client grouping fallback | ✅ | ✅ | — | ✅ Done | [Landing §3](/en/platform/applications) |
| 6 | Delete (in-page `<Can>` only) | ✅ | ✅ | ✅ | ✅ Done | [PERM §2](/en/platform/applications/permissions) |
| 7 | Runtime enforcement: AppIdGuard + allowlist refresh | ✅ | — | ✅ | ✅ Done | [Landing §2](/en/platform/applications) |

### 6. Print Template Mapping — REMOVED (2026-09-05)

The module was deleted from the product on 2026-07-24 (carmen-platform commit
`de11377`; the backend-gateway proxy and its `print_template_mapping.*`
permission keys were removed the day before, 2026-07-23,
carmen-turborepo-backend-v2 commit `c135bb21e`). The wiki module
(`en(th)/platform/print-template-mapping.md` + 3 sub-pages) was deleted the
same day this note was added, in this plan's Task 11 — no page at that path
exists any more, so the 8 sub-processes this section used to enumerate (and
their `Doc link` cells, which pointed at those now-deleted pages) are dropped
from this checklist rather than left dangling. `template_type`/`is_default`
on `tb_report_template` plus the [Report Templates → Form
Groups](/en/platform/report-templates/form-groups) sub-page now cover the
successor functionality — see [Report Templates](/en/platform/report-templates)
§1/§5. This section is kept only so the numbering below does not shift; see
Maintenance notes for the interim-correction caveat.

### 7. News

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | List: thumbnail / status / Target / audit columns | ✅ | ✅ | ✅ | ✅ Done | [UI §2](/en/platform/news/ui-screens) |
| 2 | Create / edit (markdown editor, four-card form) | ✅ | ✅ | ✅ | ✅ Done | [UI §3](/en/platform/news/ui-screens) |
| 3 | Image upload pipeline (multipart → MinIO token → presigned) | ✅ | ✅ | — | ✅ Done | [DM §5](/en/platform/news/data-model) |
| 4 | Status lifecycle + `published_at` semantics | ✅ | ✅ | ✅ | ✅ Done | [Landing §3](/en/platform/news) |
| 5 | Targeting: global vs BU list (validation) | ✅ | ✅ | ✅ | ✅ Done | [PERM §3](/en/platform/news/permissions) |
| 6 | Soft delete (dual client-side detection) | ✅ | ✅ | ✅ | ✅ Done | [DM §5](/en/platform/news/data-model) |
| 7 | Public delivery endpoints (anonymous, BU filter rules) | ✅ | — | ✅ | ✅ Done | [Landing §2](/en/platform/news) |
| 8 | Scheduling via API (`published_at <= now()` filter) | ✅ | — | ✅ | ✅ Done | [Landing §2](/en/platform/news) |
| 9 | Upload validation divergence (GIF, dimensions) | ✅ | ✅ | ✅ | ✅ Done | [PERM §4](/en/platform/news/permissions) |

### 8. Broadcasts

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | Compose: all users (`system_all`) | ✅ | ✅ | ✅ | ✅ Done | [UI §2](/en/platform/broadcasts/ui-screens) |
| 2 | Compose: specific users (`system_users`, UserMultiSelect) | ✅ | ✅ | ✅ | ✅ Done | [UI §2.2](/en/platform/broadcasts/ui-screens) |
| 3 | Compose: business unit (`bu`, code not id) | ✅ | ✅ | ✅ | ✅ Done | [UI §2.3](/en/platform/broadcasts/ui-screens) |
| 4 | Type presets + custom (`SYS_*`/`BU_*` resolution) | ✅ | ✅ | — | ✅ Done | [DM §5](/en/platform/broadcasts/data-model) |
| 5 | Scheduling semantics (read-time filter; NO cron; no cancel) | ✅ | ✅ | ✅ | ✅ Done | [PERM §3](/en/platform/broadcasts/permissions) |
| 6 | Confirmation dialog + stale-recipients leak | — | ✅ | ✅ | ✅ Done | [UI §3.1](/en/platform/broadcasts/ui-screens) |
| 7 | Delivery: socket emit + email fan-out at create time | ✅ | — | ✅ | ✅ Done | [PERM §3](/en/platform/broadcasts/permissions) |
| 8 | Recipient read/unread tracking (`tb_user_broadcast_action`) — no SPA surface | ✅ | — | — | ✅ Done | [DM §2.2](/en/platform/broadcasts/data-model) |

### 9. Report Templates

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | List: search / filter / CSV | ✅ | ✅ | ✅ | ✅ Done | [UI §2](/en/platform/report-templates/ui-screens) |
| 2 | Create / edit (tabbed Dialog/Content XML editors) | ✅ | ✅ | ✅ | ✅ Done | [UI §3–4](/en/platform/report-templates/ui-screens) |
| 3 | Dialog/Content XML format | ✅ | — | — | ✅ Done | [XML Spec](/en/platform/report-templates/xml-spec) |
| 4 | `kind` (report vs print) | ✅ | ✅ | — | ✅ Done | [Landing §3](/en/platform/report-templates) |
| 5 | Data-source binding (view / function / procedure) | ✅ | ✅ | — | ✅ Done | [DM §4](/en/platform/report-templates/data-model) |
| 6 | Per-BU scoping (allow/deny) | ✅ | ✅ | ✅ | ✅ Done | [DM](/en/platform/report-templates/data-model) |
| 7 | Preview / db-objects probe | — | ✅ | — | ✅ Done | [UI §4.4](/en/platform/report-templates/ui-screens) |
| 8 | Permission gates (`report_template.*`, delete in-page only) | — | — | ✅ | ✅ Done | [PERM §2](/en/platform/report-templates/permissions) |
| 9 | Historical relation to the now-removed Print Template Mapping module (`report_group`; superseded by `template_type`/`is_default`, 2026-07-23/24) | ✅ | — | — | ✅ Done | [Landing §5](/en/platform/report-templates) |

## Table B — Single-page modules

| Module | Sub-process | Page exists? | Content complete? | Status | Doc link |
|--------|-------------|--------------|-------------------|--------|----------|
| Profile | View/edit own identity | ✅ | ✅ | ✅ Done | [Profile](/en/platform/profile) |
| Profile | Change own password (PATCH) | ✅ | ✅ | ✅ Done | [Profile §3](/en/platform/profile) |
| Profile | Gating (authenticated-only) | ✅ | ✅ | ✅ Done | [Profile §4](/en/platform/profile) |
| Changelog | JSON source + authoring flow | ✅ | ✅ | ✅ Done | [Changelog §2](/en/platform/changelog) |
| Changelog | Public page + version badges | ✅ | ✅ | ✅ Done | [Changelog §3](/en/platform/changelog) |
| Changelog | Release process (`build:bump`) | ✅ | ✅ | ✅ Done | [Changelog §4](/en/platform/changelog) |
| Shell & Dashboard | Dashboard hub (`/dashboard` — activity stream + counts rail) | ✅ | ✅ | ✅ Done | [Dashboard](/en/platform/dashboard) |
| Shell & Dashboard | Landing + Login shell (public pages) | ✅ | ✅ | ✅ Done | [Landing](/en/platform/landing); Login gate mechanics covered in [RBAC](/en/platform/rbac) + [Users lifecycle](/en/platform/users/lifecycle) — the Login screen itself has no dedicated page, matching the Dashboard/Profile treatment of bare `<PrivateRoute>` screens |

## Locale coverage (TH)

Not counted in the summary; EN is canonical. TH state as of 2026-06-11:

- **Full TH translations:** all 5 new modules as shipped by the 2026-06-10 sync (rbac, applications, print-template-mapping, news, broadcasts — 20 pages), both book landings, all 5 legacy-module landings, and report-templates data-model + permissions (backfilled). Of those 20 pages, print-template-mapping's 4 (EN+TH) were deleted along with the module on 2026-07-24 (`de11377`) — 4 of the original 5 new modules / 16 of the 20 pages remain current today.
- **TH stubs (~25 lines, deliberate 2026-05-19 deferral — corrected for accuracy 2026-06-10, not expanded):** clusters/{data-model,ui-screens,permissions}, business-units/{data-model,ui-screens}, users/{data-model,lifecycle,ui-screens}, report-templates/ui-screens. xml-spec TH is a full page.
- Expanding the stubs is a known deferred task — do not start without user confirmation.

## Maintenance notes

- Update this file whenever a platform wiki page is added/expanded or carmen-platform ships
  a new screen/flow. New SPA features add rows; recount the Summary.
- Coverage was established by the 2026-06-10 Platform Book Sync
  (`.specs/2026-06-10-platform-book-sync-plan.md`, 39 commits) with two-stage review of
  every page against SPA + backend source.
- **Closed 2026-07-29:** the Dashboard hub and public Landing page gaps (Table B, Shell &
  Dashboard) — see [Dashboard](/en/platform/dashboard) and [Landing](/en/platform/landing).
  Project total was 86/86 (100%) at that point.
- **Interim correction, 2026-09-05 (Task 11 of the 2026-09-05 Platform re-sync):** the
  Print Template Mapping row, its §6 sub-process table, and its source-map row were
  removed because the module and its wiki page were deleted from the product 2026-07-24
  (`de11377`); the Summary total was patched from 86 to 78 by subtracting its 8
  sub-processes, not by re-deriving the other 11 modules' counts. This file is still due
  a full rewrite against current carmen-platform HEAD (a later task in the 2026-09-05
  Platform re-sync plan) — treat every number here as provisional until that task runs.
- **Not tracked in this file's tables (by design — none are one of the 11 named Platform
  units):** three screens carmen-platform shipped after this checklist's 2026-06-11
  baseline — [Tenant Migrations](/en/platform/business-units/tenant-migrations)
  (`/tenant-migrations`, 2026-06-30, documented as a Business Units sub-page),
  [SQL Workbench](/en/platform/sql-workbench) (`/sql-workbench`, 2026-07-09, standalone page),
  and [Form Groups](/en/platform/report-templates/form-groups) (`/report-form-groups`,
  2026-07-24, documented as a Report Templates sub-page, replacing the grouped-card list
  of the print-template-mapping module that carmen-platform deleted the same day, commit
  `de11377` — the module's own wiki page was removed in Task 11, 2026-09-05). All three
  screens above are fully documented; they
  are omitted from the Summary/Table A/Table B structure only because that structure is
  scoped to the 11 named units plus Table B's single-page modules, and these three don't
  fit either category cleanly — same treatment the pre-existing sub-pages (data-model,
  ui-screens, permissions, xml-spec, lifecycle) already get.
- carmen-platform moves fast — verify against `src/App.tsx` HEAD before trusting any
  row here; SITEMAP.md in that repo lags.
