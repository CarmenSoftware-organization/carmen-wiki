# Carmen Platform — Process Coverage Checklist

Internal tracker (not a published Wiki.js page). Enumerates every Carmen Platform
admin-SPA process by module — sourced from the **carmen-platform SPA source**
(`src/App.tsx`, `src/pages/`, `src/services/`, `src/components/nav/`) and the
**Prisma platform schema** / **micro-cronjobs schema** — and records whether the
wiki documents it. Answers: "is the Platform documentation project finished?".
Sibling of `.specs/process-coverage-checklist.md` (Inventory book); kept separate
because the two books use different page structures and sources of truth.

How to read: each row is a sub-process. **DM/UI/PERM** = covered in the module's
`data-model` / `ui-screens` / `permissions` page(s); for a module with fewer than
three sub-pages, the relevant axis is documented on the module's own landing page
instead, and content there counts toward whichever axis it serves. Symbols:
✅ complete · 🟡 partial/stub · ⬜ missing · — axis not applicable to this row.
Tracks the **EN locale** (canonical); TH state is summarized in "Locale coverage."

## Summary (full rewrite — as of 2026-09-06, against carmen-platform HEAD `157a65e`, 2026-09-04 17:51:42 +0700)

This replaces the 2026-06-11-dated summary and its 2026-09-05 interim patch
(86 → 78 sub-processes). Both prior numbers measured a June snapshot of the SPA
that predates 16 modules this plan added and 1 module (`print-template-mapping`)
it removed. **This rewrite is a full re-enumeration against the current book and
the current SPA, not an adjustment of the old totals** — see "How this was
counted" below for method and the arithmetic reconciliation.

**Book size, verified from the filesystem, not estimated:** `find en/platform -name '*.md' | wc -l` and the `th/` equivalent both return **74**, and `en/`/`th/` trees are identical file-for-file (diffed by path list). Of the 29 top-level pages under `en/platform/`: **20** own a sub-page folder (Table A), **4** are landing-only modules with no sub-pages because the depth rule gave them none (`platform-migrations`, `report-form-groups`, `super-admins`, `usage-analytics` — Table B), and **5** are standalone pages that are not modules at all (`changelog`, `dashboard`, `landing`, `profile`, `sql-workbench` — Table C). 20 + 4 + 5 = 29 pages = **24 modules** + **5 standalone pages**. `74` reconciles as 29 top-level pages + 45 sub-pages (Table A's 20 modules hold 1–5 sub-pages each; see the module list below).

| Module | Sub-processes | Done | Partial | Not yet | % rows ✅ (sampled check) |
|--------|--------------:|-----:|--------:|--------:|-----------:|
| **Table A — modules with a sub-page folder** | | | | | |
| Clusters | 10 | 10 | 0 | 0 | 100% |
| Business Units | 11 | 11 | 0 | 0 | 100% |
| Users | 10 | 10 | 0 | 0 | 100% |
| Platform RBAC | 8 | 8 | 0 | 0 | 100% |
| Applications | 9 | 9 | 0 | 0 | 100% |
| Broadcasts | 12 | 12 | 0 | 0 | 100% |
| News | 10 | 10 | 0 | 0 | 100% |
| Report Templates | 11 | 11 | 0 | 0 | 100% |
| Licenses | 9 | 9 | 0 | 0 | 100% |
| License Catalog | 8 | 8 | 0 | 0 | 100% |
| Cluster Admin | 8 | 8 | 0 | 0 | 100% |
| Platform Config | 9 | 9 | 0 | 0 | 100% |
| Email Settings | 6 | 6 | 0 | 0 | 100% |
| User Platform | 6 | 6 | 0 | 0 | 100% |
| Feature Flags | 6 | 6 | 0 | 0 | 100% |
| Tenant Migrations | 6 | 6 | 0 | 0 | 100% |
| Tenant Imports | 7 | 7 | 0 | 0 | 100% |
| Activity Events | 6 | 6 | 0 | 0 | 100% |
| Database Pools | 7 | 7 | 0 | 0 | 100% |
| Cronjobs | 8 | 8 | 0 | 0 | 100% |
| **Table A subtotal** | **167** | **167** | **0** | **0** | **100%** |
| **Table B — landing-only modules** | | | | | |
| Platform Migrations | 7 | 7 | 0 | 0 | 100% |
| Report Form Groups | 6 | 6 | 0 | 0 | 100% |
| Super Admins | 6 | 6 | 0 | 0 | 100% |
| Usage Analytics | 7 | 7 | 0 | 0 | 100% |
| **Table B subtotal** | **26** | **26** | **0** | **0** | **100%** |
| **Table C — standalone pages (not modules)** | | | | | |
| Changelog | 3 | 3 | 0 | 0 | 100% |
| Dashboard | 3 | 3 | 0 | 0 | 100% |
| Landing | 3 | 3 | 0 | 0 | 100% |
| Profile | 3 | 3 | 0 | 0 | 100% |
| SQL Workbench | 6 | 6 | 0 | 0 | 100% |
| **Table C subtotal** | **18** | **18** | **0** | **0** | **100%** |
| **Project total** | **211** | **211** | **0** | **0** | **100%** |

**Read the 100% figures above as a full enumeration, checked on a sample:**
every one of the 211 rows was enumerated from the current pages and given a
doc link, but only **19 of the 74 files were read in full** to confirm their
content actually covers what the row claims — the other 55 were checked at
section-header level only. "100%" means no gap was found in that sample, not
that all 211 rows were individually re-verified this pass. See "Depth of
verification" under "How this was counted," immediately below, for the exact
file list and what "checked at header level" did and did not confirm.

Arithmetic check: 167 + 26 + 18 = 211, matching the "Project total" row; each
module's own Done+Partial+Not-yet also sums to its own Sub-processes count. No
`print-template-mapping` row appears anywhere in this file — the module was
deleted from the product on 2026-07-24 (`de11377`) and its wiki page removed in
this plan's Task 11; its historical replacement (`is_default`/`template_type` on
`tb_report_template`, plus this book's own [Report Form Groups](/en/platform/report-form-groups)
module) is covered under Report Templates row 11 and the Report Form Groups
Table B rows.

### How this was counted

- **Method:** for each module, sub-processes were enumerated from the `##`/`###`
  section headers of its current landing page and every sub-page (captured
  directly from the files on disk, not from any prior version of this checklist
  or from the resync plan's own estimates — the brief for this task flagged two
  prior module/page counts in this same plan as wrong, so this rewrite treats
  the filesystem as the only count source). Status was then judged by reading
  the corresponding section content, not by assuming a header implies coverage.
- **Depth of verification:** 19 of the 74 files were read in full for this
  task — a stratified sample covering every module shape in the book (a
  5-sub-page module, 3-sub-page modules, 2-sub-page modules, 1-sub-page
  modules, all four Table B landing-only modules, and one Table C page) —
  specifically `cluster-admin/ui-screens`, `user-platform/permissions`,
  `tenant-imports`, `license-catalog/data-model`, `license-catalog/ui-screens`,
  `database-pools/data-model`, `database-pools/ui-screens`,
  `feature-flags/data-model`, `activity-events/data-model`, `platform-config`,
  `email-settings`, `super-admins`, `tenant-migrations`, `platform-migrations`,
  `usage-analytics`, `report-form-groups`, `sql-workbench`,
  `business-units/tenant-migrations`, and `cronjobs/data-model`. Every one of
  these files was found to carry cited, section-specific detail (file:line
  references, dated commits, edge-case tables, "Recommendations" sections)
  rather than placeholder or stub text. The remaining 55 files were checked at
  the section-header level only (every `#`/`##`/`###` line, for both EN and
  TH) — not read in full for this task.
- **Bound on this claim:** "no gaps found" describes the 19 files read in full
  plus the header-level consistency of the other 55 (comparable header density
  and section shapes throughout, no file with only 1–2 trivial headers outside
  the deliberately short standalone pages in Table C). It is not a line-by-line
  audit of all 74 files — a module marked ✅ here should still be spot-checked
  again by whoever next touches it, per this file's own "Maintenance notes."
- **Cross-checked against the resync's own record:** for the 8 modules this
  plan re-verified rather than wrote from scratch (Clusters, Business Units,
  Users, Platform RBAC, Applications, Broadcasts, News, Report Templates), this
  file also drew on `.specs/resync-platform-2026-09-05-progress.md`'s per-module
  task rows (2–9), which documented specific drift found and fixed, page by
  page, during this same plan — those rows independently corroborate that the
  current pages reflect current SPA behavior, not the June baseline.
- **TH locale is excluded from every percentage above**, per this file's
  standing convention (EN is canonical) — see "Locale coverage (TH)" below for
  what is and is not a full TH mirror today.

## How status is judged

- **DM / UI / PERM cell:** `✅` usable section exists and was checked against
  either full-file reading or header-level review · `🟡` mentioned but
  incomplete/stub · `⬜` not found · `—` axis not applicable (no SPA surface, no
  data persistence, or no permission gate exists for this sub-process).
- **Overall row Status:** `✅ Done` all applicable cells ✅ · `🟡 Partial` some
  but not all ✅ · `⬜ Not yet` all applicable cells ⬜.
- Sub-processes are derived from the SPA at carmen-platform HEAD `157a65e`
  (2026-09-04 17:51:42 +0700, confirmed via `git rev-parse --short HEAD` /
  `git log -1 --format=%ci` run against `../carmen-platform` for this task) and
  the backend at HEAD `937cf5ac4` (2026-09-06, as cited throughout the pages
  themselves). New SPA features add rows here; this file is due for another
  pass whenever either HEAD moves meaningfully.

## Source mapping

| Wiki module | Routes | Components | Permission key(s) | Feature key | e2e suite |
|---|---|---|---|---|---|
| clusters | `/clusters`, `/clusters/new`, `/clusters/:id/edit` | `ClusterManagement`, `ClusterEdit` | `cluster.read` (nav; also gates business-units and tenant-migrations) + create/update/delete | `clusters` | `clusters` (stale — pre-dates the Aug/Sep redesign) |
| business-units | `/business-units`, `/business-units/new`, `/business-units/:id/edit` | `BusinessUnitManagement`, `BusinessUnitEdit` | `cluster.read` (nav; shares the Clusters resource) | `business_units` | `business-units` (stale) |
| users | `/users`, `/users/new`, `/users/:id/edit` | `UserManagement`, `UserEdit` | `user.read` (nav) + create/update/delete | `users` | `users` (stale) |
| rbac | `/platform/roles[...]`, `/platform/category-permissions` | `RoleManagement`, `RoleEdit`, `PermissionCatalog` | `platform_role.read`/create/update/delete; category-permissions ungated on the frontend | `platform_roles` | `roles`, `permission-catalog` (stale) |
| applications | `/applications`, `/applications/new`, `/applications/:id/edit` | `ApplicationManagement`, `ApplicationEdit` | `application.read` (nav) + create/update/delete | `applications` | `applications` (stale) |
| broadcasts | `/broadcasts`, `/broadcasts/new`, `/broadcasts/:id/edit` | `BroadcastManagement`, `BroadcastCompose`, `BroadcastEdit` | `broadcast.read`/`.send`/`.update`/`.delete` | `broadcasts` | `broadcast` (1 spec, not stale — Compose only) |
| news | `/news`, `/news/new`, `/news/:id/edit` | `NewsManagement`, `NewsEdit` | `news.read` (nav) + create/update/delete | `news` | `news` (one broken locator) |
| report-templates | `/report-templates[...]` | `ReportTemplateManagement`, `ReportTemplateEdit` | `report_template.read` (nav) + create/update/delete | `report_templates` | `report-templates` (one confirmed-broken create test) |
| licenses | `/licenses[...]`, `/licenses/:clusterId`, subscription/seat/BU-quota forms | `LicenseCenter`, `ClusterLicenseDetail`, `SubscriptionForm`, `LicensePurchaseForm` | `subscription.read` (nav) + `subscription.manage` | `licenses` | none |
| license-catalog | `/license-features`, `/license-feature-groups[...]` | `LicenseCatalog` (2 tabs), `LicenseFeatureGroupEdit` | `license_feature.read`/`.manage`; `license_feature_group.read`/`.manage` | `license_features`, `license_feature_groups` | none |
| cluster-admin | `/cluster-admin[...]` (6 sub-routes) | `ClusterAdminEntry`, `ClusterProfile`, `BusinessUnitList`, `BusinessUnitForm`, `ClusterUsers`, `ClusterAdminLicenses` | none — membership via `isClusterAdminOf`, no RBAC key | `cluster_admin_cluster`/`_business_units`/`_licenses`/`_users` | none |
| platform-config | `/platform/configs` | `PlatformConfigManagement` | `platform_config.read`/`.manage` (+ `license.manage` and super-admin for 2 of 9 cards) | `platform_config` | none |
| email-settings | `/platform/email-settings` | `EmailSettingManagement` | `email_setting.read`/`.manage` (Routing card also needs `platform_config.*`) | `email_settings` | none |
| user-platform | `/platform/user-platform[...]` | `UserPlatformManagement`, `UserPlatformEdit` | `user_platform.read`/`.manage` (detail page also depends on Users' `user.read`) | `user_platform` | `user-platform` |
| super-admins | `/platform/super-admins` | `SuperAdminManagement` | none — `superAdminOnly: true`, no permission string | `super_admins` | `super-admins` (fixture-level failure, pre-dates the 2026-09-02 rewrite) |
| feature-flags | `/platform/features` | `FeatureFlagManagement` | `feature_flag.manage` (nav; no separate `.read`) | none (deliberately ungated) | none |
| tenant-migrations | `/tenant-migrations` | `TenantMigrationManagement`, `FleetSync`, `DeployConsole` | `cluster.read` (nav, reused) + super-admin/deploy-token on every action | `tenant_migrations` | none |
| tenant-imports | `/tenant-imports` | `TenantImportWizard` | `data_import.manage` (nav; no separate `.read`) | `tenant_imports` | none |
| usage-analytics | `/analytics` | `UsageAnalytics`, `StatCards`, `TopList`, `UsageChart` | `activity_event.read` (nav) + `.detail` (drill-down) | `usage_analytics` | none |
| activity-events | `/activity-events` | `ActivityEventManagement`, `EventDetailSheet` | `activity_event.detail` (nav) | `activity_events` | none |
| platform-migrations | `/platform/migrations` | `PlatformMigrationManagement`, `OpRow`, `RunConsole` | none — `superAdminOnly: true`, or deploy-token at the backend | `platform_migrations` | none |
| database-pools | `/platform/database-pools[...]` | `DatabasePoolManagement`, `DatabasePoolEdit` | `database_pool.read`/`.manage` | `database_pools` | none |
| cronjobs | `/cronjobs[...]` | `CronJobManagement`, `CronJobEdit` | `cronjob.read`/`.manage` | `cronjobs` | none |
| report-form-groups | `/report-form-groups` | `ReportFormGroupManagement`, `GroupCard` | `report_template.read`/`.create`/`.update` (reused; no dedicated key) | `report_form_groups` | none |
| sql-workbench | `/sql-workbench` | `SqlWorkbench` | `sql_workbench.read`/`.manage` | `sql_workbench` | none |
| dashboard | `/dashboard` | `Dashboard` | none — visible to anyone with platform authority | none | `dashboard` |
| landing | `/` | `Landing` | none — public route | none | `landing` |
| profile | `/profile` (shared with `/cluster-admin/:clusterId/profile`) | `Profile` | none — acts on the caller's own account | none | `profile` |
| changelog | `/changelog` | `Changelog` | none — public route | none | `changelog` |

## Table A — Modules with a sub-page folder

### 1. Clusters — `en/platform/clusters/{data-model,permissions,ui-screens}.md`

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | List: search/filter, Fleet Capacity band, CSV export | — | ✅ | ✅ | ✅ Done | [UI §2](/en/platform/clusters/ui-screens) |
| 2 | Create cluster (opening BU-quota licence required, `ClusterDraftPlate` preview) | ✅ | ✅ | ✅ | ✅ Done | [UI §3](/en/platform/clusters/ui-screens) |
| 3 | View/edit: `ClusterPlate` header + 3-tab body (Licensing/Business Units/Users) | ✅ | ✅ | ✅ | ✅ Done | [UI §4](/en/platform/clusters/ui-screens) |
| 4 | Soft delete + Deleted badge | ✅ | ✅ | ✅ | ✅ Done | [UI §2, §5.4](/en/platform/clusters/ui-screens) |
| 5 | Branding: logo/avatar upload | — | ✅ | ✅ | ✅ Done | [UI §4.1](/en/platform/clusters/ui-screens) |
| 6 | License caps via `tb_cluster_license` ledger / `v_cluster_bu_quota` view | ✅ | ✅ | — | ✅ Done | [DM §2.4](/en/platform/clusters/data-model) |
| 7 | Cluster users: add/edit/remove (`parent_bu_id` removed — no BU field) | ✅ | ✅ | ✅ | ✅ Done | [UI §5](/en/platform/clusters/ui-screens) |
| 8 | Add BU from cluster page (`?cluster_id=` preselect) | — | ✅ | ✅ | ✅ Done | [UI §4.3](/en/platform/clusters/ui-screens) |
| 9 | View History (`activity_log.read`) — cross-cutting, new since June baseline | — | ✅ | ✅ | ✅ Done | [PERM §8](/en/platform/clusters/permissions) |
| 10 | Platform-authority resolution layer + audit columns (`everEdited` precedence) | ✅ | ✅ | ✅ | ✅ Done | [PERM §5](/en/platform/clusters/permissions) |

### 2. Business Units — `en/platform/business-units/{data-model,tenant-migrations,ui-screens}.md`

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | List: filters/CSV, `BrandMark` avatar, Overview strip | ✅ | ✅ | ✅ | ✅ Done | [UI §2](/en/platform/business-units/ui-screens) |
| 2 | Create BU + opening license check flow (no `code` field — backend-generated) | ✅ | ✅ | ✅ | ✅ Done | [UI §3](/en/platform/business-units/ui-screens) |
| 3 | Edit: 6-tab document (General/Location/Formats/Technical/Users/Licenses) | ✅ | ✅ | ✅ | ✅ Done | [UI §4](/en/platform/business-units/ui-screens) |
| 4 | Technical tab: database-pool/schema repoint (new — `db_connection` dropped) | ✅ | ✅ | — | ✅ Done | [DM §2.4](/en/platform/business-units/data-model) |
| 5 | BU users tab: add/edit/remove | ✅ | ✅ | ✅ | ✅ Done | [UI §4.6](/en/platform/business-units/ui-screens) |
| 6 | Licenses tab — split out of Users (PR #276), New Subscription button | ✅ | ✅ | ✅ | ✅ Done | [UI §4.7](/en/platform/business-units/ui-screens) |
| 7 | Per-BU Tenant Migrations card (embedded; fleet-wide screen lives elsewhere) | — | ✅ | ✅ | ✅ Done | [Tenant Migrations sub-page](/en/platform/business-units/tenant-migrations) |
| 8 | Soft delete | ✅ | ✅ | ✅ | ✅ Done | [UI §2.4, §5.4](/en/platform/business-units/ui-screens) |
| 9 | Module activation join (`tb_business_unit_tb_module`) — schema-only | ✅ | — | — | ✅ Done | [DM §2.2](/en/platform/business-units/data-model) |
| 10 | `cluster.*` key-reuse gotcha (no dedicated `business_unit.*` keys) | — | — | ✅ | ✅ Done | [Landing](/en/platform/business-units) |
| 11 | Audit columns + View History (`activity_log.read`) | ✅ | ✅ | ✅ | ✅ Done | [UI §2.5](/en/platform/business-units/ui-screens) |

### 3. Users — `en/platform/users/{data-model,lifecycle,ui-screens}.md`

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | List: collapsed identity column, asymmetric Status, filters/CSV, Directory strip | ✅ | ✅ | ✅ | ✅ Done | [UI §2](/en/platform/users/ui-screens) |
| 2 | Create user (sectioned form; firstname/lastname now required) | ✅ | ✅ | ✅ | ✅ Done | [Lifecycle §2](/en/platform/users/lifecycle) |
| 3 | Edit user (view mode has no separate Details card — Hero absorbs it) | ✅ | ✅ | ✅ | ✅ Done | [UI §4](/en/platform/users/ui-screens) |
| 4 | Access card (`UserAccessTree`) — merged Clusters + Business Units, new | ✅ | ✅ | ✅ | ✅ Done | [UI §4.2](/en/platform/users/ui-screens) |
| 5 | Admin password reset (`<Can permission="user.update">`-gated) | ✅ | ✅ | ✅ | ✅ Done | [Lifecycle §6](/en/platform/users/lifecycle) |
| 6 | Keycloak sync | ✅ | ✅ | — | ✅ Done | [Lifecycle §7](/en/platform/users/lifecycle) |
| 7 | Soft delete + hard delete | ✅ | ✅ | ✅ | ✅ Done | [Lifecycle §5](/en/platform/users/lifecycle) |
| 8 | Bulk soft delete / bulk hard delete (super-admin only) — new | ✅ | ✅ | ✅ | ✅ Done | [Lifecycle §5.3](/en/platform/users/lifecycle) |
| 9 | Login gate / effective permissions resolution | ✅ | — | ✅ | ✅ Done | [DM §5](/en/platform/users/data-model) |
| 10 | Audit columns + View History (`activity_log.read`) | ✅ | ✅ | ✅ | ✅ Done | [UI §2.5](/en/platform/users/ui-screens) |

### 4. Platform RBAC — `en/platform/rbac/{data-model,permissions,ui-screens}.md`

Scope note: this module's own pages document **Roles + Permission Catalog** at
full depth; Super Admins and User Platform are covered at summary level only
(by design, per the plan's split) and are counted under their own Table A/B
modules below, not repeated here.

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | Permission catalog browse (`PermissionCatalog`, resource-grouped) | ✅ | ✅ | ✅ | ✅ Done | [UI §3](/en/platform/rbac/ui-screens) |
| 2 | Role create/edit — `PermissionGrid` (replaced accordion `PermissionPicker`, 2026-08-20) | ✅ | ✅ | ✅ | ✅ Done | [UI §2.6](/en/platform/rbac/ui-screens) |
| 3 | Role delete (client-ungated — Roles list exception) | — | ✅ | ✅ | ✅ Done | [PERM §2](/en/platform/rbac/permissions) |
| 4 | `platform_role.*` rename + `/platform/category-permissions` route move | ✅ | — | ✅ | ✅ Done | [DM §5](/en/platform/rbac/data-model) |
| 5 | `RoleIdentityHero` view-mode pattern (Settings card renders only while editing) | — | ✅ | — | ✅ Done | [UI §2.2](/en/platform/rbac/ui-screens) |
| 6 | Effective permissions + `checkPermission` resolution walkthrough | ✅ | — | ✅ | ✅ Done | [PERM §4](/en/platform/rbac/permissions) |
| 7 | Bootstrap exception (user count ≤ 1) | — | — | ✅ | ✅ Done | [PERM §5](/en/platform/rbac/permissions) |
| 8 | Gate composition (route/sidebar/`<Can>`) incl. legacy migration | — | — | ✅ | ✅ Done | [PERM §3](/en/platform/rbac/permissions) |

### 5. Applications — `en/platform/applications/{data-model,permissions,ui-screens}.md`

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | List: search/status filter/CSV, App ID column, Registry strip (dedicated endpoint) | ✅ | ✅ | ✅ | ✅ Done | [UI §2](/en/platform/applications/ui-screens) |
| 2 | Access column redesign — `ApplicationReachCell` bar+fraction (2026-09-02) | ✅ | ✅ | — | ✅ Done | [UI §2.3](/en/platform/applications/ui-screens) |
| 3 | Create application | ✅ | ✅ | ✅ | ✅ Done | [UI §3.1](/en/platform/applications/ui-screens) |
| 4 | Edit + API Names selector (authority-verb tinting, stale-grant accounting) | ✅ | ✅ | ✅ | ✅ Done | [UI §3.4](/en/platform/applications/ui-screens) |
| 5 | `allow_all` vs explicit list (replace semantics) | ✅ | ✅ | ✅ | ✅ Done | [DM §5.1](/en/platform/applications/data-model) |
| 6 | Delete (in-page `<Can>` only) | — | ✅ | ✅ | ✅ Done | [PERM §2](/en/platform/applications/permissions) |
| 7 | View History (`activity_log.read`) — new since June baseline | — | ✅ | ✅ | ✅ Done | [PERM §2](/en/platform/applications/permissions) |
| 8 | Runtime enforcement: `AppIdGuard` + allowlist refresh | ✅ | — | ✅ | ✅ Done | [PERM §3](/en/platform/applications/permissions) |
| 9 | Audit precedence via shared `auditColumns()`/`normalizeAudit()` | ✅ | ✅ | — | ✅ Done | [UI §2.3](/en/platform/applications/ui-screens) |

### 6. Broadcasts — `en/platform/broadcasts/{data-model,permissions,ui-screens}.md`

The module's shape changed the most of any in this book since the June
baseline: the single compose-only screen became three (List/Compose/Edit),
following an August notification redesign.

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | List screen (`BroadcastManagement`) — new screen entirely | — | ✅ | ✅ | ✅ Done | [UI §2](/en/platform/broadcasts/ui-screens) |
| 2 | Compose: all users (`system_all`) | ✅ | ✅ | ✅ | ✅ Done | [UI §3.1](/en/platform/broadcasts/ui-screens) |
| 3 | Compose: specific users (`system_users`, `UserMultiSelect`) | ✅ | ✅ | ✅ | ✅ Done | [UI §3.1](/en/platform/broadcasts/ui-screens) |
| 4 | Compose: business unit (`bu`, code not id) | ✅ | ✅ | ✅ | ✅ Done | [UI §3.1](/en/platform/broadcasts/ui-screens) |
| 5 | Type presets + custom (decorative; stored in `metadata.severity`) | ✅ | ✅ | — | ✅ Done | [UI §3.3](/en/platform/broadcasts/ui-screens) |
| 6 | Mandatory expiry (`end_at` now required; computed `status`) | ✅ | ✅ | — | ✅ Done | [DM §2.1](/en/platform/broadcasts/data-model) |
| 7 | Edit screen (`BroadcastEdit`) — new screen; content lock while `scheduled` | ✅ | ✅ | ✅ | ✅ Done | [PERM §4](/en/platform/broadcasts/permissions) |
| 8 | Optimistic locking (`doc_version`, 409 on mismatch) | ✅ | ✅ | — | ✅ Done | [PERM §4](/en/platform/broadcasts/permissions) |
| 9 | Scheduling semantics: `ScheduleWorker` for `system_users` only | ✅ | — | ✅ | ✅ Done | [PERM §3](/en/platform/broadcasts/permissions) |
| 10 | Delivery: socket emit at create time; email fan-out removed | ✅ | — | — | ✅ Done | [DM §5](/en/platform/broadcasts/data-model) |
| 11 | Recipient read/unread tracking (`tb_user_broadcast_action`) — no SPA surface | ✅ | — | — | ✅ Done | [DM §2.2](/en/platform/broadcasts/data-model) |
| 12 | Permission gates: `broadcast.read`/`.send`/`.update`/`.delete` | — | ✅ | ✅ | ✅ Done | [PERM §2](/en/platform/broadcasts/permissions) |

### 7. News — `en/platform/news/{data-model,permissions,ui-screens}.md`

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | List: thumbnail/status/Target/audit columns | ✅ | ✅ | ✅ | ✅ Done | [UI §2](/en/platform/news/ui-screens) |
| 2 | `NewsroomSummary` (dedicated summary endpoint, 2026-08-24) | ✅ | ✅ | — | ✅ Done | [UI §2.2](/en/platform/news/ui-screens) |
| 3 | Bulk selection toolbar | — | ✅ | ✅ | ✅ Done | [UI §2.5](/en/platform/news/ui-screens) |
| 4 | Create/edit (markdown editor, four-card form) | ✅ | ✅ | ✅ | ✅ Done | [UI §3](/en/platform/news/ui-screens) |
| 5 | Image upload pipeline (multipart → MinIO token → presigned) | ✅ | ✅ | — | ✅ Done | [DM §2.1](/en/platform/news/data-model) |
| 6 | Status lifecycle + `published_at` semantics | ✅ | ✅ | ✅ | ✅ Done | [DM §2.2](/en/platform/news/data-model) |
| 7 | Targeting: global vs BU list validation | ✅ | ✅ | ✅ | ✅ Done | [PERM §3](/en/platform/news/permissions) |
| 8 | Soft delete (dual client-side detection) | ✅ | ✅ | ✅ | ✅ Done | [DM §2.1](/en/platform/news/data-model) |
| 9 | Server-side write/read enforcement asymmetry (writes gated 2026-08-20; reads deliberately open for `mobile-app`) | — | — | ✅ | ✅ Done | [PERM §1](/en/platform/news/permissions) |
| 10 | View History (`activity_log.read`) — new since June baseline | — | ✅ | ✅ | ✅ Done | [PERM §2](/en/platform/news/permissions) |

### 8. Report Templates — `en/platform/report-templates/{data-model,form-groups,permissions,ui-screens,xml-spec}.md`

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | List: search/filter/CSV | — | ✅ | ✅ | ✅ Done | [UI §2](/en/platform/report-templates/ui-screens) |
| 2 | Create/edit (tabbed Dialog/Content XML editors) | ✅ | ✅ | ✅ | ✅ Done | [UI §3–4](/en/platform/report-templates/ui-screens) |
| 3 | Dialog/Content XML format | ✅ | — | — | ✅ Done | [XML Spec](/en/platform/report-templates/xml-spec) |
| 4 | `kind`/`template_type` (report vs print/form) | ✅ | ✅ | — | ✅ Done | [DM §4](/en/platform/report-templates/data-model) |
| 5 | Data-source binding (view/function/procedure) | ✅ | ✅ | — | ✅ Done | [DM §5.3](/en/platform/report-templates/data-model) |
| 6 | Per-BU scoping (allow/deny) | ✅ | ✅ | ✅ | ✅ Done | [PERM §7](/en/platform/report-templates/permissions) |
| 7 | Preview/db-objects probe | — | ✅ | — | ✅ Done | [UI §4.7](/en/platform/report-templates/ui-screens) |
| 8 | `PageHeader` audit line (Metadata card removed 2026-08-22) | — | ✅ | — | ✅ Done | [UI §4.3](/en/platform/report-templates/ui-screens) |
| 9 | Permission gates (`report_template.*`; empty-state Add is gated, not merely disabled) | — | — | ✅ | ✅ Done | [PERM §7](/en/platform/report-templates/permissions) |
| 10 | Historical relation to the removed Print Template Mapping module | ✅ | — | — | ✅ Done | [Landing §3](/en/platform/report-templates) |
| 11 | `report-form-groups` sub-page vs. the new top-level module (cross-reference) | — | ✅ | — | ✅ Done | [Form Groups sub-page](/en/platform/report-templates/form-groups) |

### 9. Licenses — `en/platform/licenses/{data-model,permissions,ui-screens}.md`

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | `LicenseCenter` Fleet Capacity band | ✅ | ✅ | — | ✅ Done | [UI §2.1](/en/platform/licenses/ui-screens) |
| 2 | Four-tab switch (By cluster / subscription / seat / BU quota) | ✅ | ✅ | — | ✅ Done | [UI §2.2](/en/platform/licenses/ui-screens) |
| 3 | `ClusterLicenseDetail` (health strip + 3-tab shared timeline) | ✅ | ✅ | — | ✅ Done | [UI §3](/en/platform/licenses/ui-screens) |
| 4 | `SubscriptionForm` (feature-group entitlements, not individual features) | ✅ | ✅ | ✅ | ✅ Done | [UI §4](/en/platform/licenses/ui-screens) |
| 5 | `LicensePurchaseForm` (seat license / BU quota) | ✅ | ✅ | ✅ | ✅ Done | [UI §5](/en/platform/licenses/ui-screens) |
| 6 | Legacy `/subscriptions*` redirects | — | ✅ | — | ✅ Done | [UI §6](/en/platform/licenses/ui-screens) |
| 7 | Expiry thresholds (configurable window, cross-module) | ✅ | — | — | ✅ Done | [DM §6](/en/platform/licenses/data-model) |
| 8 | Two capacity views (`v_cluster_bu_cap` vs `v_cluster_bu_quota`) | ✅ | — | — | ✅ Done | [DM §3](/en/platform/licenses/data-model) |
| 9 | Permission gates (`subscription.read`/`.manage`; two purchase-form routes need only `.read`) | — | — | ✅ | ✅ Done | [PERM §3](/en/platform/licenses/permissions) |

### 10. License Catalog — `en/platform/license-catalog/{data-model,ui-screens}.md`

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | Shell tab mechanics (tabs are routes, remount on switch) | — | ✅ | ✅ | ✅ Done | [UI §2](/en/platform/license-catalog/ui-screens) |
| 2 | Feature catalog browse + `state` toggle (active/inactive/hide) | ✅ | ✅ | ✅ | ✅ Done | [UI §3](/en/platform/license-catalog/ui-screens) |
| 3 | Hide-confirmation with `affected_bu_count`/descendant impact | ✅ | ✅ | — | ✅ Done | [DM §3](/en/platform/license-catalog/data-model) |
| 4 | Bundle CRUD (`GroupCatalogPanel`) | ✅ | ✅ | ✅ | ✅ Done | [UI §4](/en/platform/license-catalog/ui-screens) |
| 5 | Bundle editor (`LicenseFeatureGroupEdit`) | ✅ | ✅ | ✅ | ✅ Done | [UI §5](/en/platform/license-catalog/ui-screens) |
| 6 | n-tier tree shape + `sort_order` banding (2026-09-03 restructuring) | ✅ | — | — | ✅ Done | [DM §3](/en/platform/license-catalog/data-model) |
| 7 | `affected_bu_count` computation (deliberately includes expired subscriptions) | ✅ | — | — | ✅ Done | [DM §6](/en/platform/license-catalog/data-model) |
| 8 | Permission gates (two tab-specific pairs + cross-module dependency) | — | ✅ | ✅ | ✅ Done | [Landing §4](/en/platform/license-catalog) |

### 11. Cluster Admin — `en/platform/cluster-admin/{permissions,ui-screens}.md`

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | Entry/landing redirect logic (single-cluster vs. multi-cluster vs. zero) | — | ✅ | — | ✅ Done | [UI §2](/en/platform/cluster-admin/ui-screens) |
| 2 | `ClusterProfile` — capacity strip, identity/branding, narrowed fields | — | ✅ | ✅ | ✅ Done | [UI §3](/en/platform/cluster-admin/ui-screens) |
| 3 | `BusinessUnitList` — no create action, Over-limit rank badge | — | ✅ | ✅ | ✅ Done | [UI §4](/en/platform/cluster-admin/ui-screens) |
| 4 | `BusinessUnitForm` — 5-tab document (Overview/People/Hotel/Company/Configuration) | — | ✅ | ✅ | ✅ Done | [UI §5](/en/platform/cluster-admin/ui-screens) |
| 5 | `ClusterUsers` — Members/Invitations tabs | — | ✅ | ✅ | ✅ Done | [UI §6](/en/platform/cluster-admin/ui-screens) |
| 6 | `ClusterAdminLicenses` — confirmed read-only, no write path anywhere | — | ✅ | ✅ | ✅ Done | [UI §7](/en/platform/cluster-admin/ui-screens) |
| 7 | No RBAC permission anywhere — membership (`isClusterAdminOf`) is the whole check | — | — | ✅ | ✅ Done | [PERM §3](/en/platform/cluster-admin/permissions) |
| 8 | Mid-session 403 pattern (`ClusterAccessLost`) — 4 of 6 screens implement it | — | ✅ | ✅ | ✅ Done | [PERM §4](/en/platform/cluster-admin/permissions) |

### 12. Platform Config — `en/platform/platform-config/data-model.md`

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | Invitation card (`base_url`/`expiry_days`) | ✅ | ✅ | ✅ | ✅ Done | [Landing §3.2](/en/platform/platform-config) |
| 2 | Rate Limits card (`invitation`, other half — in-memory per-process caveat) | ✅ | ✅ | ✅ | ✅ Done | [Landing §3.2](/en/platform/platform-config) |
| 3 | Sign-up / Email Verification / Password Reset cards (`LinkConfigCard`) | ✅ | ✅ | ✅ | ✅ Done | [Landing §3.2](/en/platform/platform-config) |
| 4 | Notification Email card — no confirmed consumer, flagged not asserted | ✅ | ✅ | ✅ | ✅ Done | [Landing §3.2](/en/platform/platform-config) |
| 5 | License Enforcement card (platform-wide kill switch) | ✅ | ✅ | ✅ | ✅ Done | [Landing §3.2, §4.3](/en/platform/platform-config) |
| 6 | Expiry Thresholds card (display-only; separate permission-free reader) | ✅ | ✅ | ✅ | ✅ Done | [Landing §4.4](/en/platform/platform-config) |
| 7 | Platform Migration card (super-admin-only write; deploy-token machine path preserved) | ✅ | ✅ | ✅ | ✅ Done | [Landing §3.2](/en/platform/platform-config) |
| 8 | `license.manage` conjunction (lives here, not in Licenses) | — | ✅ | ✅ | ✅ Done | [Landing §4.3](/en/platform/platform-config) |
| 9 | Two registry keys never shown on this screen (`email_routing`, `feature_flags`) | ✅ | — | ✅ | ✅ Done | [Landing §3.5](/en/platform/platform-config) |

### 13. Email Settings — `en/platform/email-settings/data-model.md`

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | Sender profile CRUD (`tb_email_sender_profile`, named list) | ✅ | ✅ | ✅ | ✅ Done | [Landing §1](/en/platform/email-settings) |
| 2 | Email Routing card (5 flows → profile mapping) | ✅ | ✅ | ✅ | ✅ Done | [Landing §3.2](/en/platform/email-settings) |
| 3 | Password handling (masked, patch-preserves-on-blank semantics) | ✅ | ✅ | — | ✅ Done | [Landing §3.4](/en/platform/email-settings) |
| 4 | Send test email | — | ✅ | ✅ | ✅ Done | [Landing §3.5](/en/platform/email-settings) |
| 5 | Flow-to-consumer trace (register/verify_email/forgot_password/invitation/notification) | ✅ | — | — | ✅ Done | [Landing §3.2](/en/platform/email-settings) |
| 6 | Cross-module permission trap — `platform_config.read` without `.manage` | — | ✅ | ✅ | ✅ Done | [Landing §4.2–4.3](/en/platform/email-settings) |

### 14. User Platform — `en/platform/user-platform/{permissions,ui-screens}.md`

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | Registry list (`UserPlatformManagement`) | — | ✅ | ✅ | ✅ Done | [UI §2](/en/platform/user-platform/ui-screens) |
| 2 | Per-holder dossier (`UserPlatformEdit`) | — | ✅ | ✅ | ✅ Done | [UI §3](/en/platform/user-platform/ui-screens) |
| 3 | Grant/revoke access | — | ✅ | ✅ | ✅ Done | [PERM §2](/en/platform/user-platform/permissions) |
| 4 | Add/remove per-assignment role | — | ✅ | ✅ | ✅ Done | [PERM §2](/en/platform/user-platform/permissions) |
| 5 | Inactive-holder + email-unverified surfacing | — | ✅ | — | ✅ Done | [Landing §3.3–3.4](/en/platform/user-platform) |
| 6 | `user.read` cross-module gap, traced end to end | — | ✅ | ✅ | ✅ Done | [PERM §3](/en/platform/user-platform/permissions) |

### 15. Feature Flags — `en/platform/feature-flags/data-model.md`

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | `FEATURE_CATALOG` — 28 keys across two consoles | ✅ | ✅ | — | ✅ Done | [DM §3](/en/platform/feature-flags/data-model) |
| 2 | Frontend consumers (nav filtering, `hide`/`inactive`/`comingSoon`) | — | ✅ | — | ✅ Done | [DM §5](/en/platform/feature-flags/data-model) |
| 3 | Backend enforcement (`GET` ungated, `PUT` gated `feature_flag.manage`) | ✅ | — | ✅ | ✅ Done | [DM §4](/en/platform/feature-flags/data-model) |
| 4 | Whole-map `PUT` semantics — no `PATCH`, omitted key is deleted | ✅ | ✅ | ✅ | ✅ Done | [DM §4](/en/platform/feature-flags/data-model) |
| 5 | Orphan-key detection UI | — | ✅ | — | ✅ Done | [Landing §4](/en/platform/feature-flags) |
| 6 | Edge cases (last-write-wins on the whole map; fail-open on fetch failure) | ✅ | — | — | ✅ Done | [DM §6](/en/platform/feature-flags/data-model) |

### 16. Tenant Migrations — `en/platform/tenant-migrations/data-model.md`

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | Fleet Sync summary + BU table (Check/Apply/Deploy all) | — | ✅ | ✅ | ✅ Done | [Landing §3.1](/en/platform/tenant-migrations) |
| 2 | Deploy Console (streamed batch progress) | — | ✅ | — | ✅ Done | [Landing §3.1](/en/platform/tenant-migrations) |
| 3 | Kill switch (`TENANT_MIGRATION_API_ENABLED`) + CI deploy-token path | — | — | ✅ | ✅ Done | [Landing §3.4, §4](/en/platform/tenant-migrations) |
| 4 | Migration-state derivation — no persisted status; Prisma CLI text-matched | ✅ | — | — | ✅ Done | [DM §2](/en/platform/tenant-migrations/data-model) |
| 5 | Relationship to the embedded per-BU card (shared service, same gate) | — | ✅ | ✅ | ✅ Done | [Landing §3.5](/en/platform/tenant-migrations) |
| 6 | Non-bypassable backend gate (super-admin or deploy-token; not RBAC) | — | — | ✅ | ✅ Done | [Landing §4.2](/en/platform/tenant-migrations) |

### 17. Tenant Imports — `en/platform/tenant-imports/ui-screens.md`

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | Pick Business Unit screen | — | ✅ | — | ✅ Done | [UI §2](/en/platform/tenant-imports/ui-screens) |
| 2 | Upload Workbook screen | — | ✅ | — | ✅ Done | [UI §3](/en/platform/tenant-imports/ui-screens) |
| 3 | File Check screen | — | ✅ | — | ✅ Done | [UI §4](/en/platform/tenant-imports/ui-screens) |
| 4 | Steps screen (`StepRail`/`StepPanel`, preview → import) | — | ✅ | — | ✅ Done | [UI §5](/en/platform/tenant-imports/ui-screens) |
| 5 | Twelve-step catalog + duplicate-key/coercion rules | ✅ | — | — | ✅ Done | [Landing §3.1–3.2](/en/platform/tenant-imports) |
| 6 | Company Profile step — platform-DB write, `AppIdGuard`-only permission seam | ✅ | ✅ | ✅ | ✅ Done | [Landing §3.5](/en/platform/tenant-imports) |
| 7 | Permission gate (`data_import.manage`, no separate `.read` tier) | — | — | ✅ | ✅ Done | [Landing §4](/en/platform/tenant-imports) |

### 18. Activity Events — `en/platform/activity-events/data-model.md`

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | Explorer screen: columns/sorting, filters/search, CSV export | — | ✅ | ✅ | ✅ Done | [Landing §3](/en/platform/activity-events) |
| 2 | Row detail sheet | — | ✅ | — | ✅ Done | [Landing §3.3](/en/platform/activity-events) |
| 3 | Retention (365-day job) + daily rollup | ✅ | — | — | ✅ Done | [DM §4](/en/platform/activity-events/data-model) |
| 4 | Enriched read-time fields (`user_name`/`user_email`/`app_name`) | ✅ | — | — | ✅ Done | [DM §3](/en/platform/activity-events/data-model) |
| 5 | Permission gate (`activity_event.detail`) vs. Usage Analytics' `.read` | — | — | ✅ | ✅ Done | [Landing §4](/en/platform/activity-events) |
| 6 | Distinction from `tb_activity` (the separate View History audit table) | ✅ | — | — | ✅ Done | [DM header](/en/platform/activity-events/data-model) |

### 19. Database Pools — `en/platform/database-pools/{data-model,ui-screens}.md`

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | List: composed DSN column, copy-to-clipboard, filters, CSV | ✅ | ✅ | ✅ | ✅ Done | [UI §2](/en/platform/database-pools/ui-screens) |
| 2 | Create pool | ✅ | ✅ | ✅ | ✅ Done | [UI §3](/en/platform/database-pools/ui-screens) |
| 3 | Edit pool (read/edit toggle; password never revealed) | ✅ | ✅ | ✅ | ✅ Done | [UI §4](/en/platform/database-pools/ui-screens) |
| 4 | Delete (in-use protection, up to 10 blocking BUs named) | ✅ | ✅ | ✅ | ✅ Done | [DM §3](/en/platform/database-pools/data-model) |
| 5 | Password encryption/masking lifecycle | ✅ | ✅ | — | ✅ Done | [DM §4](/en/platform/database-pools/data-model) |
| 6 | Relationship to Business Units / Tenant Migrations connection resolution | ✅ | — | — | ✅ Done | [DM §5](/en/platform/database-pools/data-model) |
| 7 | Permission gate (`database_pool.read` on every route; `.manage` on writes) | — | ✅ | ✅ | ✅ Done | [DM §6](/en/platform/database-pools/data-model) |

### 20. Cronjobs — `en/platform/cronjobs/{data-model,ui-screens}.md`

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | List: stat band, filters, columns, CSV export | — | ✅ | ✅ | ✅ Done | [UI §2](/en/platform/cronjobs/ui-screens) |
| 2 | Create/edit job (Basics/Schedule/Execution/Type Config) | ✅ | ✅ | ✅ | ✅ Done | [UI §3](/en/platform/cronjobs/ui-screens) |
| 3 | Six job types' configs (report/notification/cleanup/dashboard_refresh/activity_rollup/activity_retention) | ✅ | ✅ | — | ✅ Done | [DM §3](/en/platform/cronjobs/data-model) |
| 4 | Scheduler mechanics (polling, reconciliation, retry, concurrency cap) | ✅ | — | — | ✅ Done | [DM §4](/en/platform/cronjobs/data-model) |
| 5 | Delete-job confirm | — | ✅ | ✅ | ✅ Done | [UI §5.1](/en/platform/cronjobs/ui-screens) |
| 6 | Where failures surface (list icon, edit page gap, SigNoz) | ✅ | ✅ | — | ✅ Done | [DM §5](/en/platform/cronjobs/data-model) |
| 7 | Foreign-owned banner / ownership check (now dead code on the gateway) | ✅ | ✅ | — | ✅ Done | [DM §6](/en/platform/cronjobs/data-model) |
| 8 | Permission gate (`cronjob.read`/`.manage`) | — | ✅ | ✅ | ✅ Done | [Landing §4](/en/platform/cronjobs) |

**Table A subtotal: 167 sub-processes, 167 Done, 0 Partial, 0 Not yet.**

## Table B — Landing-only modules (no sub-page folder)

### 21. Platform Migrations — `en/platform/platform-migrations.md`

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | Status/Deploy card (`prisma migrate deploy` against the platform DB) | ✅ | ✅ | ✅ | ✅ Done | [§1, §3.3](/en/platform/platform-migrations) |
| 2 | Resolve-a-stuck-migration card | ✅ | ✅ | ✅ | ✅ Done | [§3.3](/en/platform/platform-migrations) |
| 3 | Seed data catalog (8 seed operations, safety-to-rerun stated per op) | ✅ | ✅ | ✅ | ✅ Done | [§3.3](/en/platform/platform-migrations) |
| 4 | Drift check catalog (5 read-only + 1 hidden, writing check) | ✅ | ✅ | ✅ | ✅ Done | [§3.3](/en/platform/platform-migrations) |
| 5 | Multi-BU picker for `seed-role-permission` (tenant app-roles, not platform RBAC) | ✅ | ✅ | — | ✅ Done | [§3.4](/en/platform/platform-migrations) |
| 6 | Two-authority gate (deploy-token or super-admin) behind `platform_migration.api_enabled` | — | — | ✅ | ✅ Done | [§3.1, §4](/en/platform/platform-migrations) |
| 7 | Shared concurrency lock across migrations + seeds (per-process, not per-cluster) | ✅ | — | — | ✅ Done | [§3.2](/en/platform/platform-migrations) |

### 22. Report Form Groups — `en/platform/report-form-groups.md`

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | Fetching/grouping (paged fetch, bucket by `report_group`) | ✅ | ✅ | — | ✅ Done | [§3.1](/en/platform/report-form-groups) |
| 2 | Group card (per-group template list, compact audit line, status badges) | ✅ | ✅ | ✅ | ✅ Done | [§3.2](/en/platform/report-form-groups) |
| 3 | Set-as-default flow (confirm dialog, two-step non-transactional `PUT`) | ✅ | ✅ | ✅ | ✅ Done | [§3.3](/en/platform/report-form-groups) |
| 4 | Fixed (12 canonical codes) vs. legacy groups | ✅ | ✅ | — | ✅ Done | [§3.4](/en/platform/report-form-groups) |
| 5 | Permission reuse — shares `report_template.*`, separate feature key | — | ✅ | ✅ | ✅ Done | [§4](/en/platform/report-form-groups) |
| 6 | Historical succession from the removed Print Template Mapping module | ✅ | — | — | ✅ Done | [§2](/en/platform/report-form-groups) |

### 23. Super Admins — `en/platform/super-admins.md`

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | Roster screen (card list, search past an 8-row threshold) | — | ✅ | ✅ | ✅ Done | [§3.1](/en/platform/super-admins) |
| 2 | Add super admin (`UserPicker`, 409-on-duplicate handling) | — | ✅ | ✅ | ✅ Done | [§3.2](/en/platform/super-admins) |
| 3 | Remove super admin + self-removal UI-only guard | — | ✅ | ✅ | ✅ Done | [§3.3](/en/platform/super-admins) |
| 4 | `superAdminOnly` gate — no RBAC permission key anywhere in the module | — | — | ✅ | ✅ Done | [§1, §4](/en/platform/super-admins) |
| 5 | `tb_platform_super_admin` entity, incl. audit-trail gap (no `created_by_id`) | ✅ | — | — | ✅ Done | [§5](/en/platform/super-admins) |
| 6 | Effect on an already-open session (stale `isSuperAdmin` cache is cosmetic only) | — | — | ✅ | ✅ Done | [§5.4](/en/platform/super-admins) |

### 24. Usage Analytics — `en/platform/usage-analytics.md`

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | Filter bar (date range/BU/Application/Event type) + 90-day window cap | — | ✅ | — | ✅ Done | [§3.1](/en/platform/usage-analytics) |
| 2 | Five StatCards (events/clicks/page views/sessions/active users) | ✅ | ✅ | — | ✅ Done | [§3.2](/en/platform/usage-analytics) |
| 3 | Daily area chart (sessions/users only) + CSV export (all four series) | ✅ | ✅ | — | ✅ Done | [§3.3](/en/platform/usage-analytics) |
| 4 | Top Pages list + drill-down to Activity Events | ✅ | ✅ | ✅ | ✅ Done | [§3.4, §4.2](/en/platform/usage-analytics) |
| 5 | Top Elements list (never clickable) | ✅ | ✅ | — | ✅ Done | [§3.5](/en/platform/usage-analytics) |
| 6 | Permission seam (`activity_event.read` vs `.detail`) + cluster scoping | — | — | ✅ | ✅ Done | [§4](/en/platform/usage-analytics) |
| 7 | Empty-state vs. error-state distinction | — | ✅ | — | ✅ Done | [§3.7](/en/platform/usage-analytics) |

**Table B subtotal: 26 sub-processes, 26 Done, 0 Partial, 0 Not yet.**

## Table C — Standalone pages (not modules)

| Page | Sub-process | Page exists? | Content complete? | Status | Doc link |
|------|-------------|--------------|-------------------|--------|----------|
| Changelog | JSON source + authoring flow | ✅ | ✅ | ✅ Done | [Changelog §2](/en/platform/changelog) |
| Changelog | Public page + version badges | ✅ | ✅ | ✅ Done | [Changelog §3](/en/platform/changelog) |
| Changelog | Notable product removals (incl. Print Template Mapping) | ✅ | ✅ | ✅ Done | [Changelog §6](/en/platform/changelog) |
| Dashboard | Activity stream | ✅ | ✅ | ✅ Done | [Dashboard §2](/en/platform/dashboard) |
| Dashboard | Counts rail | ✅ | ✅ | ✅ Done | [Dashboard §3](/en/platform/dashboard) |
| Dashboard | What's not on the dashboard (scope boundary) | ✅ | ✅ | ✅ Done | [Dashboard §4](/en/platform/dashboard) |
| Landing | Page content + "Inside the Console" index | ✅ | ✅ | ✅ Done | [Landing §2–3](/en/platform/landing) |
| Landing | Confirmed drift: index vs. real sidebar | ✅ | ✅ | ✅ Done | [Landing §4](/en/platform/landing) |
| Landing | Roles/personas + gating (public route) | ✅ | ✅ | ✅ Done | [Landing §5](/en/platform/landing) |
| Profile | View/edit own identity, mounted at two routes | ✅ | ✅ | ✅ Done | [Profile §1](/en/platform/profile) |
| Profile | Change own password | ✅ | ✅ | ✅ Done | [Profile §3](/en/platform/profile) |
| Profile | Gating (authenticated-only) | ✅ | ✅ | ✅ Done | [Profile §4](/en/platform/profile) |
| SQL Workbench | BU switcher + connection bar | ✅ | ✅ | ✅ Done | [§3](/en/platform/sql-workbench) |
| SQL Workbench | DB object tree (tables/views/procedures/functions) | ✅ | ✅ | ✅ Done | [§3](/en/platform/sql-workbench) |
| SQL Workbench | SQL editor + Run, destructive-statement confirmation | ✅ | ✅ | ✅ Done | [§3](/en/platform/sql-workbench) |
| SQL Workbench | Save (create/replace view/procedure/function) + Drop | ✅ | ✅ | ✅ Done | [§3](/en/platform/sql-workbench) |
| SQL Workbench | Result panel (virtual scroll, CSV export) | ✅ | ✅ | ✅ Done | [§3](/en/platform/sql-workbench) |
| SQL Workbench | Permission gate — read/manage split; 2026-08-20 backend gap closed | ✅ | ✅ | ✅ Done | [§4](/en/platform/sql-workbench) |

**Table C subtotal: 18 sub-processes, 18 Done, 0 Partial, 0 Not yet.**

## Locale coverage (TH)

Not counted in the summary; EN is canonical. Verified this task by comparing
EN/TH line counts for all 74 file pairs (a page under half its EN sibling's
line count was treated as a stub and spot-read to confirm).

- **EN and TH trees are file-for-file identical** — same 74 paths in both
  locales, confirmed by directory listing.
- **All 16 modules new to this plan's 2026-09-05 round are full TH mirrors**
  (100% line-count ratio against their EN sibling, for every one of their
  landing + sub-pages) — `activity-events`, `applications` region already
  full from an earlier sync, `broadcasts`, `cluster-admin`, `cronjobs`,
  `database-pools`, `email-settings`, `feature-flags`, `license-catalog`,
  `licenses`, `platform-config`, `platform-migrations`, `report-form-groups`,
  `sql-workbench`, `super-admins`, `tenant-imports`, `tenant-migrations`,
  `usage-analytics`, `user-platform`.
- **10 pre-existing sub-pages remain deliberate ~25–37-line TH stubs**
  (2026-05-19 deferral, corrected for factual accuracy on 2026-06-10/2026-09-06
  passes but never expanded — do not start expanding without user
  confirmation): `clusters/{data-model,permissions,ui-screens}`,
  `business-units/{data-model,ui-screens}`,
  `users/{data-model,lifecycle,ui-screens}`, `report-templates/ui-screens`,
  and — **newly confirmed this task** — `report-templates/xml-spec`.
- **Correction to the prior version of this file:** the previous "Locale
  coverage" section stated "`xml-spec` TH is a full page." That was checked
  directly this task (`th/platform/report-templates/xml-spec.md`, 26 lines
  against the EN page's 208, and its own body is literally a 3-item "TODO"
  list dated 2026-05-19) and is **wrong** — `xml-spec` TH is a stub like its
  nine siblings above, not a full mirror. This file now lists 10 TH stubs,
  not 9.
- Expanding any of the 10 stubs is a known deferred task — do not start
  without user confirmation.

## Maintenance notes

- Update this file whenever a platform wiki page is added/expanded or
  carmen-platform ships a new screen/flow. New SPA features add rows; recount
  the Summary and re-run the arithmetic check.
- Coverage was originally established by the 2026-06-10 Platform Book Sync
  (`.specs/2026-06-10-platform-book-sync-plan.md`, 39 commits), then rewritten
  in full by the 2026-09-05 Platform re-sync
  (`.specs/2026-09-05-platform-resync-design.md`, Task 30 of that plan) — this
  file. The 2026-09-05 plan added 16 new modules (Table A rows 9–20 minus the
  8 pre-existing modules, plus all of Table B and `sql-workbench` in Table C),
  removed 1 (`print-template-mapping`, deleted from the product 2026-07-24),
  and re-verified all 8 modules that existed before it (Table A rows 1–8)
  against source that had drifted well beyond the June baseline in every one
  of them — see `.specs/resync-platform-2026-09-05-progress.md` rows 2–9 for
  the itemized drift found and fixed per module.
- **This file's own prior failure mode, stated so it is not repeated:** the
  2026-06-11 total (86, then 100%) aged silently for three months with no
  measurement-date discipline attached to the number itself, and a mid-plan
  patch (86 → 78, when `print-template-mapping` was deleted) fixed only the
  one row that changed rather than re-deriving the rest — leaving every other
  module's count "provisional" by the prior version's own admission. This
  rewrite states its source HEAD in the Summary heading precisely so the next
  person can tell, without guessing, whether this file is still current
  against `../carmen-platform` before trusting any number in it.
- carmen-platform moves fast — verify against `src/App.tsx` HEAD before
  trusting any row here; `SITEMAP.md` in that repo lags.
