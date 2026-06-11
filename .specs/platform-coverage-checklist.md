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

## Summary (as of 2026-06-11)

| Module | Sub-processes | Done | Partial | Not yet | % complete |
|--------|--------------:|-----:|--------:|--------:|-----------:|
| Clusters | 9 | 9 | 0 | 0 | 100% |
| Business Units | 10 | 10 | 0 | 0 | 100% |
| Users | 10 | 10 | 0 | 0 | 100% |
| Platform RBAC | 8 | 8 | 0 | 0 | 100% |
| Applications | 7 | 7 | 0 | 0 | 100% |
| Print Template Mapping | 8 | 8 | 0 | 0 | 100% |
| News | 9 | 9 | 0 | 0 | 100% |
| Broadcasts | 8 | 8 | 0 | 0 | 100% |
| Report Templates | 9 | 9 | 0 | 0 | 100% |
| Profile | 3 | 3 | 0 | 0 | 100% |
| Changelog | 3 | 3 | 0 | 0 | 100% |
| Shell & Dashboard | 2 | 0 | 1 | 1 | 0% |
| **Project total** | 86 | 84 | 1 | 1 | **98%** |

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
| print-template-mapping | PrintTemplateMappingManagement, PrintTemplateMappingEdit | printTemplateMappingService; micro-report Go (resolve, EnsureSingleDefault); micro-business print helper; Prisma `tb_print_template_mapping` |
| news | NewsManagement, NewsEdit | newsService; backend-gateway news module + micro-cluster; Prisma `tb_news` |
| broadcasts | BroadcastCompose | broadcastService; backend-gateway + micro-notification; Prisma `tb_broadcast_notification`, `tb_user_broadcast_action` |
| report-templates | ReportTemplateManagement, ReportTemplateEdit | reportTemplateService; micro-report; Prisma `tb_report_template` |
| profile | Profile | shared axios (no service file) |
| changelog | Changelog (public) | src/data/changelog.json; build:bump |
| *(undocumented)* | Dashboard, Landing, Login | — |

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

### 6. Print Template Mapping

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | Grouped-by-document-type list + filters (pattern deviation) | ✅ | ✅ | ✅ | ✅ Done | [UI §2](/en/platform/print-template-mapping/ui-screens) |
| 2 | Create mapping | ✅ | ✅ | ✅ | ✅ Done | [UI §3](/en/platform/print-template-mapping/ui-screens) |
| 3 | Edit (soft-sort template select, view/edit toggle) | ✅ | ✅ | ✅ | ✅ Done | [UI §3.3](/en/platform/print-template-mapping/ui-screens) |
| 4 | Default flag + server `EnsureSingleDefault` (warn-only) | ✅ | ✅ | ✅ | ✅ Done | [DM §6](/en/platform/print-template-mapping/data-model) |
| 5 | Allow/deny BU lists + `resolve` semantics | ✅ | ✅ | ✅ | ✅ Done | [PERM §3](/en/platform/print-template-mapping/permissions) |
| 6 | Document types (hard-coded Go list, server-validated) | ✅ | ✅ | — | ✅ Done | [Landing §3](/en/platform/print-template-mapping) |
| 7 | Known gap: main print path bypasses BU scoping (8 services + PR) | ✅ | — | ✅ | ✅ Done | [PERM §3](/en/platform/print-template-mapping/permissions) |
| 8 | 10-row silent truncation / SPA can't clear BU lists | ✅ | ✅ | ✅ | ✅ Done | [DM §5](/en/platform/print-template-mapping/data-model) |

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
| 9 | Relation to Print Template Mapping (`report_group`) | ✅ | — | — | ✅ Done | [Landing §5](/en/platform/report-templates) |

## Table B — Single-page modules

| Module | Sub-process | Page exists? | Content complete? | Status | Doc link |
|--------|-------------|--------------|-------------------|--------|----------|
| Profile | View/edit own identity | ✅ | ✅ | ✅ Done | [Profile](/en/platform/profile) |
| Profile | Change own password (PATCH) | ✅ | ✅ | ✅ Done | [Profile §3](/en/platform/profile) |
| Profile | Gating (authenticated-only) | ✅ | ✅ | ✅ Done | [Profile §4](/en/platform/profile) |
| Changelog | JSON source + authoring flow | ✅ | ✅ | ✅ Done | [Changelog §2](/en/platform/changelog) |
| Changelog | Public page + version badges | ✅ | ✅ | ✅ Done | [Changelog §3](/en/platform/changelog) |
| Changelog | Release process (`build:bump`) | ✅ | ✅ | ✅ Done | [Changelog §4](/en/platform/changelog) |
| Shell & Dashboard | Dashboard hub (`/dashboard` — summary cards) | ⬜ | ⬜ | ⬜ Not yet | — |
| Shell & Dashboard | Landing + Login shell (public pages) | 🟡 | 🟡 | 🟡 Partial | Login gate covered in [RBAC](/en/platform/rbac) + [Users lifecycle](/en/platform/users/lifecycle); Landing page itself undocumented |

## Locale coverage (TH)

Not counted in the summary; EN is canonical. TH state as of 2026-06-11:

- **Full TH translations:** all 5 new modules (rbac, applications, print-template-mapping, news, broadcasts — 20 pages), both book landings, all 5 legacy-module landings, and report-templates data-model + permissions (backfilled).
- **TH stubs (~25 lines, deliberate 2026-05-19 deferral — corrected for accuracy 2026-06-10, not expanded):** clusters/{data-model,ui-screens,permissions}, business-units/{data-model,ui-screens}, users/{data-model,lifecycle,ui-screens}, report-templates/ui-screens. xml-spec TH is a full page.
- Expanding the stubs is a known deferred task — do not start without user confirmation.

## Maintenance notes

- Update this file whenever a platform wiki page is added/expanded or carmen-platform ships
  a new screen/flow. New SPA features add rows; recount the Summary.
- Coverage was established by the 2026-06-10 Platform Book Sync
  (`.specs/2026-06-10-platform-book-sync-plan.md`, 39 commits) with two-stage review of
  every page against SPA + backend source.
- The only open gaps: the Dashboard hub page and the public Landing page (Table B,
  Shell & Dashboard). Both are small; Dashboard is the natural next page if the SPA's
  dashboard gains real content beyond summary cards.
- carmen-platform moves fast — verify against `src/App.tsx` HEAD before trusting any
  row here; SITEMAP.md in that repo lags.
