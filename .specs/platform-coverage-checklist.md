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

## Summary (full rewrite as of 2026-09-06 against carmen-platform HEAD `157a65e`; **incrementally updated 2026-09-22 against HEAD `f1c69f1`, 2026-09-22 12:32:33 +0700** — 20 commits / 78 files of SPA drift folded in, rows 2.12–2.13, 9.10–9.11, 10.9–10.10, 16.7–16.8 added, several existing rows re-worded; EN only, TH deferred; **incrementally updated again 2026-10-27 against carmen-backstage HEAD `8405788f`** — see the 2026-10-27 note below; the SPA was renamed carmen-platform → carmen-backstage in between)

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
| Clusters | 12 | 12 | 0 | 0 | 100% |
| Business Units | 15 | 15 | 0 | 0 | 100% |
| Users | 11 | 11 | 0 | 0 | 100% |
| Platform RBAC | 10 | 10 | 0 | 0 | 100% |
| Applications | 11 | 11 | 0 | 0 | 100% |
| Broadcasts | 12 | 12 | 0 | 0 | 100% |
| News | 10 | 10 | 0 | 0 | 100% |
| Report Templates | 18 | 18 | 0 | 0 | 100% |
| Dashboard Templates | 7 | 7 | 0 | 0 | 100% |
| Licenses | 14 | 14 | 0 | 0 | 100% |
| License Catalog | 10 | 10 | 0 | 0 | 100% |
| Cluster Admin | 8 | 8 | 0 | 0 | 100% |
| Platform Config | 11 | 11 | 0 | 0 | 100% |
| Email Settings | 6 | 6 | 0 | 0 | 100% |
| User Platform | 6 | 6 | 0 | 0 | 100% |
| Feature Flags | 6 | 6 | 0 | 0 | 100% |
| AI Providers | 6 | 6 | 0 | 0 | 100% |
| Tenant Migrations | 9 | 9 | 0 | 0 | 100% |
| Tenant Seed | 7 | 7 | 0 | 0 | 100% |
| Tenant Imports | 7 | 7 | 0 | 0 | 100% |
| Activity Events | 6 | 6 | 0 | 0 | 100% |
| Database Pools | 7 | 7 | 0 | 0 | 100% |
| Cronjobs | 10 | 10 | 0 | 0 | 100% |
| **Table A subtotal** | **219** | **219** | **0** | **0** | **100%** |
| **Table B — landing-only modules** | | | | | |
| Platform Migrations | 7 | 7 | 0 | 0 | 100% |
| Report Form Groups | 6 | 6 | 0 | 0 | 100% |
| Super Admins | 7 | 7 | 0 | 0 | 100% |
| Usage Analytics | 7 | 7 | 0 | 0 | 100% |
| **Table B subtotal** | **27** | **27** | **0** | **0** | **100%** |
| **Table C — standalone pages (not modules)** | | | | | |
| Changelog | 3 | 3 | 0 | 0 | 100% |
| Dashboard | 4 | 4 | 0 | 0 | 100% |
| Landing | 3 | 3 | 0 | 0 | 100% |
| Profile | 5 | 5 | 0 | 0 | 100% |
| SQL Workbench | 6 | 6 | 0 | 0 | 100% |
| **Table C subtotal** | **21** | **21** | **0** | **0** | **100%** |
| **Project total** | **267** | **267** | **0** | **0** | **100%** |

**Read the 100% figures above as a full enumeration, checked on a sample:**
every one of the 211 rows was enumerated from the current pages and given a
doc link, but only **19 of the 74 files were read in full** to confirm their
content actually covers what the row claims — the other 55 were checked at
section-header level only. "100%" means no gap was found in that sample, not
that all 211 rows were individually re-verified this pass. See "Depth of
verification" under "How this was counted," immediately below, for the exact
file list and what "checked at header level" did and did not confirm.

Arithmetic check: 219 + 27 + 21 = **267** (2026-10-27; was 175 + 26 + 18 = 219 after the 2026-09-22 update and 167 + 26 + 18 = 211 before it), matching the "Project total" row; each
module's own Done+Partial+Not-yet also sums to its own Sub-processes count. No
`print-template-mapping` row appears anywhere in this file — the module was
deleted from the product on 2026-07-24 (`de11377`) and its wiki page removed in
this plan's Task 11; its historical replacement (`is_default`/`template_type` on
`tb_report_template`, plus this book's own [Report Form Groups](/en/platform/report-form-groups)
module) is covered under Report Templates row 11 and the Report Form Groups
Table B rows.

### 2026-10-27 incremental update (carmen-backstage `8405788f`, carmen-turborepo-backend `c9d788829`)

Source HEADs: **carmen-backstage `8405788f`** (baseline: carmen-platform `f1c69f1`) and **carmen-turborepo-backend `c9d788829`** (baseline `ef4d6f08f`), 2026-10-27. Between the two baselines the product was renamed platform → backstage (backend `e0eaeff61`, SPA `318949a3`): routes moved `/platform/*` → `/backstage/*`, permission keys `platform_*` → `backstage_*`, "Platform Config" → "Backstage Config", "Platform Migrations" → "Backstage Migrations". Module names in this file keep their original headings so existing cross-references stay valid; the wiki pages themselves carry the new names.

**Previous totals, kept as history:** 219 (2026-09-22: A 175 + B 26 + C 18) · 211 (2026-09-06) · 86 → 78 (June / 2026-09-05 interim). **New total: 267** (A 219 + B 27 + C 21), all ✅.

| Change | Rows |
|--------|-----:|
| 3 new Table A modules (AI Providers 6, Dashboard Templates 7, Tenant Seed 7) | +20 |
| Existing Table A modules: Clusters +2, Business Units +2, Users +1, Platform RBAC +2, Applications +2, Report Templates +7, Licenses +3, Platform Config +2, Tenant Migrations +1, Cronjobs +2 | +24 |
| Table B: Super Admins +1 | +1 |
| Table C: Dashboard +1, Profile +2 | +3 |
| **Total added** | **+48** |

Arithmetic: 175 + 20 + 24 = 219 (Table A) · 26 + 1 = 27 (Table B) · 18 + 3 = 21 (Table C) · 219 + 27 + 21 = **267** = 219 (previous total) + 48.
Done 267 · Partial 0 · Not yet 0 → 267 / 267 = **100%**.

Book size, re-measured from the filesystem: `find en/platform -name '*.md' | wc -l` = **84** (was 74); 32 top-level pages (29 + 3 new) = 23 modules with a sub-page folder + 4 landing-only modules + 5 standalone pages; 52 sub-pages (45 + 7). `th/platform` still holds 74 files, so the three new modules are EN-only (see "Locale coverage").

Re-worded in place (no row added): Platform Migrations row 3 (`seed-report-template-upload` dropped — 8 seeds, not 9), Cluster Admin row 6 (Seats / Modules / Interface sub-tabs), License Catalog row 10 (112 rows / 13 root areas, new `ai` root), Email Settings row 5 (`notification` flow goes through micro-notification `POST /v1/emails`). The "Dashboard hub + Landing page" gaps listed in the pre-September summary are closed: Table C Dashboard and Landing rows are ✅ against the current `dashboard.md` (home hub, §2–§5) and `landing.md` (§2–§5).

Verification depth for this update: the three new modules' landing and `ui-screens` pages were read in full (plus `dashboard-templates/lifecycle` §6 and `ai-providers/data-model` §2.2); every other added row was confirmed by locating the matching section in the cited `en/platform/` page and reading it. The "19 of 74 files read in full" caveat from 2026-09-06 still applies to every row this update did not touch.

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
- **2026-10-27 update** re-based the file on carmen-backstage `8405788f` and
  carmen-turborepo-backend `c9d788829` (see the dated note under Summary). The
  `157a65e` / `937cf5ac4` HEADs above are the 2026-09-06 baseline.

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
| email-settings | `/platform/email-settings` | `EmailSettingManagement` | `email_setting.read`/`.manage` (Routing card also needs `platform_config.*`) | `email_settings` | smoke only (stale `/platform/...` path) |
| user-platform | `/platform/user-platform[...]` | `UserPlatformManagement`, `UserPlatformEdit` | `user_platform.read`/`.manage` (detail page also depends on Users' `user.read`) | `user_platform` | `user-platform` |
| super-admins | `/platform/super-admins` | `SuperAdminManagement` | none — `superAdminOnly: true`, no permission string | `super_admins` | `super-admins` (fixture-level failure, pre-dates the 2026-09-02 rewrite) |
| feature-flags | `/platform/features` | `FeatureFlagManagement` | `feature_flag.manage` (nav; no separate `.read`) | none (deliberately ungated) | none |
| tenant-migrations | `/tenant-migrations` | `TenantMigrationManagement`, `FleetSync`, `DeployConsole` | `cluster.read` (nav, reused) + super-admin/deploy-token on every action | `tenant_migrations` | none |
| tenant-imports | `/tenant-imports` | `TenantImportWizard` | `data_import.manage` (nav; no separate `.read`) | `tenant_imports` | none |
| usage-analytics | `/analytics` | `UsageAnalytics`, `StatCards`, `TopList`, `UsageChart` | `activity_event.read` (nav) + `.detail` (drill-down) | `usage_analytics` | none |
| activity-events | `/activity-events` | `ActivityEventManagement`, `EventDetailSheet` | `activity_event.detail` (nav) | `activity_events` | none |
| platform-migrations | `/platform/migrations` | `PlatformMigrationManagement`, `OpRow`, `RunConsole` | none — `superAdminOnly: true`, or deploy-token at the backend | `platform_migrations` | smoke only (stale `/platform/...` paths) |
| database-pools | `/platform/database-pools[...]` | `DatabasePoolManagement`, `DatabasePoolEdit` | `database_pool.read`/`.manage` | `database_pools` | smoke only (stale `/platform/...` path) |
| cronjobs | `/cronjobs[...]` | `CronJobManagement`, `CronJobEdit` | `cronjob.read`/`.manage` | `cronjobs` | smoke only |
| report-form-groups | `/report-form-groups` | `ReportFormGroupManagement`, `GroupCard` | `report_template.read`/`.create`/`.update` (reused; no dedicated key) | `report_form_groups` | smoke only (page renders; sidebar link) |
| sql-workbench | `/sql-workbench` | `SqlWorkbench` | `sql_workbench.read`/`.manage` | `sql_workbench` | smoke only |
| dashboard | `/dashboard` | `Dashboard` | none — visible to anyone with platform authority | none | `dashboard` |
| landing | `/` | `Landing` | none — public route | none | `landing` |
| profile | `/profile` (shared with `/cluster-admin/:clusterId/profile`) | `Profile` | none — acts on the caller's own account | none | `profile` |
| changelog | `/changelog` | `Changelog` | none — public route | none | `changelog` |
| ai-providers | `/purchase-request-ai-providers` (old `/ai-providers` redirects) | `AiProviderManagement`, `AiProviderEditDialog` | `ai_provider.read`/`.create`/`.update`/`.delete` | `ai_providers` | none |
| dashboard-templates | `/dashboard-templates` (System / BU default / Deploy tabs) | `TemplateListPanel`, `TemplateEditDialog`, `DeployPanel` | `dashboard_template.read`/`.create`/`.update`/`.delete`/`.deploy` | see page | none |
| tenant-seed | `/tenant-seeds` | `TenantSeedManagement`, `SeedFleetSummary`, `SeedSetPickerDialog` | `tenant_seed.read`/`.apply` (+ kill switch `TENANT_MIGRATION_API_ENABLED`) | `tenant_seeds` | none |

2026-10-27 note: since the platform → backstage rename the `/platform/...` routes, `platform_*` keys and `PlatformXxx` component names in the rows above are the pre-rename spellings; the SPA now serves `/backstage/...` (with a `/platform/*` redirect), uses `backstage_*` keys and `Backstage*` components. The wiki pages carry the current names.

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
| 11 | Notes tab — internal staff timeline, up to 5 files per note (10 MB each), edit / soft-delete / restore, files panel (new 2026-10-26) | ✅ | ✅ | ✅ | ✅ Done | [UI §4.6](/en/platform/clusters/ui-screens) |
| 12 | Users tab seat **Release / Restore** (`SeatActions`; no RBAC key — super admin or cluster admin; `seat.released` / `seat.restored` audit events) | — | ✅ | ✅ | ✅ Done | [UI §4.4](/en/platform/clusters/ui-screens), [Landing](/en/platform/clusters) |

### 2. Business Units — `en/platform/business-units/{data-model,tenant-migrations,ui-screens}.md`

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | List: filters/CSV, `BrandMark` avatar, Overview strip | ✅ | ✅ | ✅ | ✅ Done | [UI §2](/en/platform/business-units/ui-screens) |
| 2 | Create BU + opening license check flow (no `code` field — backend-generated) | ✅ | ✅ | ✅ | ✅ Done | [UI §3](/en/platform/business-units/ui-screens) |
| 3 | Edit: 6-tab document (General/Location/Formats/Technical/Users/Licenses) | ✅ | ✅ | ✅ | ✅ Done | [UI §4](/en/platform/business-units/ui-screens) |
| 4 | Technical tab: database-pool/schema repoint (new — `db_connection` dropped) | ✅ | ✅ | — | ✅ Done | [DM §2.4](/en/platform/business-units/data-model) |
| 5 | BU users tab: add/edit/remove | ✅ | ✅ | ✅ | ✅ Done | [UI §4.6](/en/platform/business-units/ui-screens) |
| 6 | Licenses tab — two cards since PR #287–#289: seats + this BU's subscriptions on a shared timeline, and interface (INF) licences with backend-computed `in_force` badges; New Subscription / Add interface license buttons on `subscription.manage` | ✅ | ✅ | ✅ | ✅ Done | [UI §4.7](/en/platform/business-units/ui-screens) |
| 7 | Per-BU Tenant Migrations card (embedded; fleet-wide screen lives elsewhere) | — | ✅ | ✅ | ✅ Done | [Tenant Migrations sub-page](/en/platform/business-units/tenant-migrations) |
| 8 | Soft delete | ✅ | ✅ | ✅ | ✅ Done | [UI §2.4, §5.4](/en/platform/business-units/ui-screens) |
| 9 | Module activation join (`tb_business_unit_tb_module`) — schema-only | ✅ | — | — | ✅ Done | [DM §2.2](/en/platform/business-units/data-model) |
| 10 | `cluster.*` key-reuse gotcha (no dedicated `business_unit.*` keys) | — | — | ✅ | ✅ Done | [Landing](/en/platform/business-units) |
| 11 | Audit columns + View History (`activity_log.read`) | ✅ | ✅ | ✅ | ✅ Done | [UI §2.5](/en/platform/business-units/ui-screens) |
| 12 | Interface Entitlement card removed (PR #286, 2026-09-08) — entitlement moved to `interface`-kind licence groups; Technical tab now holds two advanced cards, and the migration card gained an error panel + Resolve (PR #297) | ✅ | ✅ | ✅ | ✅ Done | [UI §4.5](/en/platform/business-units/ui-screens) |
| 13 | List: stored-page snap-back when `page_business_units` is out of range (`outOfRangePage`, PR #298) + in-memory sortable headers on the Users card / Configuration section (PR #292) | — | ✅ | — | ✅ Done | [UI §2.1, §4.4, §4.6](/en/platform/business-units/ui-screens) |
| 14 | Notes tab (7th tab) — staff-only notes + file attachments, `tb_business_unit_note`, `bu_note.view` / `bu_note.manage`, never shown to tenants (new 2026-10-26) | ✅ | ✅ | ✅ | ✅ Done | [UI §4.8](/en/platform/business-units/ui-screens), [DM §2.6](/en/platform/business-units/data-model) |
| 15 | Attachment policy section on the Technical tab (`attachment.allowed_types` / `attachment.max_size_mb` stored as `config[]` rows; tenant-side writes of `attachment.*` keys rejected) | ✅ | ✅ | — | ✅ Done | [UI §4.4](/en/platform/business-units/ui-screens), [Landing](/en/platform/business-units) |

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
| 11 | MCP tokens card (`UserMcpTokensCard`) + admin **Revoke all MCP tokens** (`user.update`; offboarding step) — new 2026-10-14 | ✅ | ✅ | ✅ | ✅ Done | [UI §4.3](/en/platform/users/ui-screens), [Lifecycle §8](/en/platform/users/lifecycle) |

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
| 9 | Access-shape strip (`AccessShapeStrip` in `RoleIdentityHero` — one tick per catalog resource, grouped by menu section) | — | ✅ | — | ✅ Done | [UI §2.6](/en/platform/rbac/ui-screens) |
| 10 | Escalation marking — granted `backstage_role.create` / `.update` and `user_backstage.manage` chips render amber (`ESCALATION_KEYS`) | — | ✅ | ✅ | ✅ Done | [UI §2.6](/en/platform/rbac/ui-screens) |

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
| 10 | Live controls: service-status filter/control (Running / Maintenance / Read-only / Disabled) and bypass users | ✅ | ✅ | ✅ | ✅ Done | [Landing §1.1](/en/platform/applications), [UI §3.5](/en/platform/applications/ui-screens) |
| 11 | App secret card — generate / rotate / reveal (masked `cas_` stub) + require-secret switch (`application.secret.manage`; `AppIdGuard` enforcement) | ✅ | ✅ | ✅ | ✅ Done | [Landing §1.1](/en/platform/applications), [UI §3.5](/en/platform/applications/ui-screens) |

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
| 12 | Export XML tab (`export_xml`, `.xml`/`.txt` upload, non-blocking validation notes) — added 2026-10 | ✅ | ✅ | — | ✅ Done | [UI §4.7](/en/platform/report-templates/ui-screens) |
| 13 | Dialog layout editor (Preview tab, edit mode on wide screens; `@dnd-kit` drag columns / ColSpan) | — | ✅ | — | ✅ Done | [UI §4.8](/en/platform/report-templates/ui-screens) |
| 14 | XML versions sheet + restore (`tb_report_template_version`) | ✅ | ✅ | ✅ | ✅ Done | [UI §5.3](/en/platform/report-templates/ui-screens), [DM §2.2](/en/platform/report-templates/data-model) |
| 15 | JSON **Backup all** / selected-row backup download + **Import** dialog (`report_template.create`) | — | ✅ | ✅ | ✅ Done | [UI §2.3–2.4, §5.4–5.5](/en/platform/report-templates/ui-screens) |
| 16 | Availability scope: costing-method filter (`calculation_methods`: `average` / `fifo` / `average_per_location`) + run / export switches (`allow_run`, `allow_export`, list templates only) | ✅ | ✅ | — | ✅ Done | [Landing §3](/en/platform/report-templates), [DM §2.1](/en/platform/report-templates/data-model) |
| 17 | EN/TH names (`name_i18n`, `description_i18n`; `name_th` field) | ✅ | ✅ | — | ✅ Done | [UI §4.1](/en/platform/report-templates/ui-screens), [DM §2.1](/en/platform/report-templates/data-model) |
| 18 | Source lineage strip under the page title (`SourceLineage`: Dialog fields → source → builder; absent in create mode) | — | ✅ | — | ✅ Done | [UI §4](/en/platform/report-templates/ui-screens) |

### 25. Dashboard Templates — `en/platform/dashboard-templates/{data-model,lifecycle,ui-screens}.md`

Section numbers 25–27 are append-only IDs (numbers 1–24 stay stable for cross-references); the three new modules sit at their Backstage-SPA nav position, not at their number. Dashboard Templates is a Content-group module; it sits after Report Templates here because Report Form Groups, its nav neighbour, lives in Table B.

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | System tab — `TemplateListPanel` (module picker, widget table, live-read system widgets, 60 s gateway cache) | ✅ | ✅ | ✅ | ✅ Done | [UI §2](/en/platform/dashboard-templates/ui-screens), [Landing §2, §3.2](/en/platform/dashboard-templates) |
| 2 | BU default tab — starter board incl. **Main** (`module: null`); allow/deny BU lists rejected on `bu_default` | ✅ | ✅ | ✅ | ✅ Done | [UI §2](/en/platform/dashboard-templates/ui-screens), [Landing §3.1–3.2](/en/platform/dashboard-templates) |
| 3 | Widget dialog (`TemplateEditDialog`) — dataset / widget type / EN-TH titles / params / BU lists / Active; catalog validation (422) | ✅ | ✅ | ✅ | ✅ Done | [UI §3–4](/en/platform/dashboard-templates/ui-screens), [Landing §3.2–3.3](/en/platform/dashboard-templates) |
| 4 | Reorder (arrows swap neighbours; whole module renumbered 10, 20, 30…) | ✅ | ✅ | ✅ | ✅ Done | [Lifecycle §4](/en/platform/dashboard-templates/lifecycle) |
| 5 | Deploy tab — per-BU status (`never` / `customized` / `outdated` / `current`), modes `skip_customized` vs `overwrite`, type-`OVERWRITE` confirm, 409 on version drift | ✅ | ✅ | ✅ | ✅ Done | [UI §5](/en/platform/dashboard-templates/ui-screens), [Lifecycle §6](/en/platform/dashboard-templates/lifecycle) |
| 6 | Global BU-default version counter (`tb_dashboard_bu_default_version`; bumped by every BU-default write, shown as a version badge) | ✅ | ✅ | — | ✅ Done | [DM §2.2](/en/platform/dashboard-templates/data-model), [UI §2.1](/en/platform/dashboard-templates/ui-screens) |
| 7 | Permission gates (`dashboard_template.read` / `.create` / `.update` / `.delete` / `.deploy`; backstage-wide guard on writes; default roles) | — | ✅ | ✅ | ✅ Done | [Landing §5](/en/platform/dashboard-templates) |


### 9. Licenses — `en/platform/licenses/{data-model,permissions,ui-screens}.md`

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | `LicenseCenter` Fleet Capacity band | ✅ | ✅ | — | ✅ Done | [UI §2.1](/en/platform/licenses/ui-screens) |
| 2 | Five-tab switch (By cluster / subscription / seat / BU quota / interface) | ✅ | ✅ | — | ✅ Done | [UI §2.2](/en/platform/licenses/ui-screens) |
| 3 | `ClusterLicenseDetail` (health strip + 3-tab shared timeline) | ✅ | ✅ | — | ✅ Done | [UI §3](/en/platform/licenses/ui-screens) |
| 4 | `SubscriptionForm` (feature-group entitlements, not individual features) | ✅ | ✅ | ✅ | ✅ Done | [UI §4](/en/platform/licenses/ui-screens) |
| 5 | `LicensePurchaseForm` (seat license / BU quota / interface — `selector: 'amount' \| 'feature-group'`) | ✅ | ✅ | ✅ | ✅ Done | [UI §5](/en/platform/licenses/ui-screens) |
| 6 | Legacy `/subscriptions*` redirects | — | ✅ | — | ✅ Done | [UI §6](/en/platform/licenses/ui-screens) |
| 7 | Expiry thresholds (configurable window, cross-module) | ✅ | — | — | ✅ Done | [DM §6](/en/platform/licenses/data-model) |
| 8 | Two capacity views (`v_cluster_bu_cap` vs `v_cluster_bu_quota`) | ✅ | — | — | ✅ Done | [DM §3](/en/platform/licenses/data-model) |
| 9 | Permission gates (`subscription.read`/`.manage`; two purchase-form routes need only `.read`) | — | — | ✅ | ✅ Done | [PERM §3](/en/platform/licenses/permissions) |
| 10 | Interface (INF) licence ledger — `tb_business_unit_interface_license`, group `kind`, union-of-windows rule, two-condition `in_force`, `GET /api/license` folding, the 2026-09-08 data loss and the 2026-09-10 guarded data migration | ✅ | ✅ | ✅ | ✅ Done | [Landing §3.6](/en/platform/licenses), [DM §2.4](/en/platform/licenses/data-model) |
| 11 | Every-column header sorting on `/licenses` tables incl. server-side `status` key (PR #290) | ✅ | ✅ | — | ✅ Done | [UI §2.5](/en/platform/licenses/ui-screens) |
| 12 | Summary band above the subscription / purchase tables (`SubscriptionSummary` clickable filter chips: All / Active / Expired / Expiring soon / Deleted) | — | ✅ | — | ✅ Done | [UI §2.4–2.5](/en/platform/licenses/ui-screens) |
| 13 | Deleted-licence view (super admin): restore and permanent (hard) delete | ✅ | ✅ | ✅ | ✅ Done | [UI §2.6](/en/platform/licenses/ui-screens) |
| 14 | Retired licence numbers (`tb_license_number_retired` — numbers of permanently deleted licences are not reused) | ✅ | — | — | ✅ Done | [DM §2.5](/en/platform/licenses/data-model) |

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
| 9 | Bundle `kind` (`standard` \| `interface`) — create-only segmented control, locked on edit, Interface badge on the list, 400 on the wrong ledger pairing | ✅ | ✅ | — | ✅ Done | [Landing §3.4](/en/platform/license-catalog), [DM §2.2, §5](/en/platform/license-catalog/data-model) |
| 10 | `LICENSE_ONLY_RESOURCES` generator set + counts re-verified 2026-10-27 at 112 rows / 13 root areas / 99 non-root / 105 active / 7 inactive (was 107/12/100/7 on 2026-09-22; new `ai` root; earlier `system_admin.period` → `inventory_period` rename) | ✅ | — | — | ✅ Done | [Landing §3.2](/en/platform/license-catalog), [DM §3](/en/platform/license-catalog/data-model) |

### 11. Cluster Admin — `en/platform/cluster-admin/{permissions,ui-screens}.md`

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | Entry/landing redirect logic (single-cluster vs. multi-cluster vs. zero) | — | ✅ | — | ✅ Done | [UI §2](/en/platform/cluster-admin/ui-screens) |
| 2 | `ClusterProfile` — capacity strip, identity/branding, narrowed fields | — | ✅ | ✅ | ✅ Done | [UI §3](/en/platform/cluster-admin/ui-screens) |
| 3 | `BusinessUnitList` — no create action, Over-limit rank badge | — | ✅ | ✅ | ✅ Done | [UI §4](/en/platform/cluster-admin/ui-screens) |
| 4 | `BusinessUnitForm` — 6-tab document (Overview/People/Hotel/Company/Configuration/Licenses — the last added PR #291 with two read-only cards, deep-linkable via `?tab=licenses`) | — | ✅ | ✅ | ✅ Done | [UI §5](/en/platform/cluster-admin/ui-screens) |
| 5 | `ClusterUsers` — Members/Invitations tabs | — | ✅ | ✅ | ✅ Done | [UI §6](/en/platform/cluster-admin/ui-screens) |
| 6 | `ClusterAdminLicenses` — still no write path; since PR #291 shows Subscriptions and Interface-licence cards (membership-checked `/clusters/:id/subscriptions`; rows link within the shell), reshaped 2026-10 into three licence-type sub-tabs (Seats / Modules / Interface; selection kept in `?license=`) | — | ✅ | ✅ | ✅ Done | [UI §7](/en/platform/cluster-admin/ui-screens) |
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
| 6 | Expiry Thresholds card (display-only; separate permission-free reader; four keys since 2026-09-09 — `interface_days` added) | ✅ | ✅ | ✅ | ✅ Done | [Landing §4.4](/en/platform/platform-config) |
| 7 | Platform Migration card (super-admin-only write; deploy-token machine path preserved) | ✅ | ✅ | ✅ | ✅ Done | [Landing §3.2](/en/platform/platform-config) |
| 8 | `license.manage` conjunction (lives here, not in Licenses) | — | ✅ | ✅ | ✅ Done | [Landing §4.3](/en/platform/platform-config) |
| 9 | Two registry keys never shown on this screen (`email_routing`, `feature_flags`) | ✅ | — | ✅ | ✅ Done | [Landing §3.5](/en/platform/platform-config) |
| 10 | Google Sign-in card (`google_sign_in`: independent `backstage` / `app` switches for the Google button and flow) | ✅ | ✅ | ✅ | ✅ Done | [Landing §3.2](/en/platform/platform-config) |
| 11 | External API card (`external_api.base_url` — public gateway root URL for external systems; page now "eleven cards, ten keys") | ✅ | ✅ | ✅ | ✅ Done | [Landing §3.1–3.2](/en/platform/platform-config) |

### 13. Email Settings — `en/platform/email-settings/data-model.md`

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | Sender profile CRUD (`tb_email_sender_profile`, named list) | ✅ | ✅ | ✅ | ✅ Done | [Landing §1](/en/platform/email-settings) |
| 2 | Email Routing card (5 flows → profile mapping) | ✅ | ✅ | ✅ | ✅ Done | [Landing §3.2](/en/platform/email-settings) |
| 3 | Password handling (masked, patch-preserves-on-blank semantics) | ✅ | ✅ | — | ✅ Done | [Landing §3.4](/en/platform/email-settings) |
| 4 | Send test email | — | ✅ | ✅ | ✅ Done | [Landing §3.5](/en/platform/email-settings) |
| 5 | Flow-to-consumer trace (register/verify_email/forgot_password/invitation/notification; `notification` goes through micro-notification `POST /v1/emails`) | ✅ | — | — | ✅ Done | [Landing §3.2](/en/platform/email-settings) |
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

### 26. AI Providers — `en/platform/ai-providers/{data-model,ui-screens}.md`

New 2026-10-27 (nav group `navGroup.ai`, after the Backstage group). Numbered 26 as an append-only ID; see the note under section 25.

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | List screen `AiProviderManagement` — columns (Provider / Opens / Default prompt / Status / Business units / Order), inactive rows shown, no search/paging | ✅ | ✅ | — | ✅ Done | [UI §2](/en/platform/ai-providers/ui-screens) |
| 2 | Create / edit dialog `AiProviderEditDialog` (identity, link, default prompt with `{items}` token, availability toggles; `code` create-only; `doc_version` conflict handling) | ✅ | ✅ | ✅ | ✅ Done | [UI §3–4](/en/platform/ai-providers/ui-screens), [Landing §3.3](/en/platform/ai-providers) |
| 3 | Validation and the `{query}` placeholder rules (https-only, `{query}` only after first `?`/`#`, 4000-char prompt; pre-filled vs copy-to-paste) | ✅ | ✅ | — | ✅ Done | [Landing §1, §3.2](/en/platform/ai-providers) |
| 4 | Delete (soft delete, global effect; per-BU settings kept but ignored; code reusable after delete) | ✅ | ✅ | ✅ | ✅ Done | [UI §2.4](/en/platform/ai-providers/ui-screens), [Landing §5](/en/platform/ai-providers) |
| 5 | BU override resolution (`tb_application_config` key `ask_ai`; visible = active AND override.enabled ?? default_enabled_for_bu; prompt = override or default) | ✅ | — | — | ✅ Done | [DM §2.2](/en/platform/ai-providers/data-model), [Landing §2](/en/platform/ai-providers) |
| 6 | Permission gates (`ai_provider.*`; writes need backstage-wide grant; default roles) | — | ✅ | ✅ | ✅ Done | [Landing §4](/en/platform/ai-providers) |


### 16. Tenant Migrations — `en/platform/tenant-migrations/data-model.md`

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | Fleet Sync summary + BU table (Check/Apply/Deploy all) | — | ✅ | ✅ | ✅ Done | [Landing §3.1](/en/platform/tenant-migrations) |
| 2 | Deploy Console (streamed batch progress) | — | ✅ | — | ✅ Done | [Landing §3.1](/en/platform/tenant-migrations) |
| 3 | Kill switch (`TENANT_MIGRATION_API_ENABLED`) + CI deploy-token path | — | — | ✅ | ✅ Done | [Landing §3.4, §4](/en/platform/tenant-migrations) |
| 4 | Migration-state derivation — no persisted status; Prisma CLI text-matched | ✅ | — | — | ✅ Done | [DM §2](/en/platform/tenant-migrations/data-model) |
| 5 | Relationship to the embedded per-BU card (shared service, same gate) | — | ✅ | ✅ | ✅ Done | [Landing §3.5](/en/platform/tenant-migrations) |
| 6 | Non-bypassable backend gate (super-admin or deploy-token; not RBAC) | — | — | ✅ | ✅ Done | [Landing §4.2](/en/platform/tenant-migrations) |
| 7 | Resolve a stuck migration from the fleet table and the per-BU card (PR #297 — `TenantMigrationResolveDialog`, name pre-filled from Prisma's error text, `rolled-back` default); closes the "no frontend caller" gap recorded 2026-09-06 | ✅ | ✅ | ✅ | ✅ Done | [Landing §3.2a](/en/platform/tenant-migrations), [DM §6](/en/platform/tenant-migrations/data-model) |
| 8 | Schema + pool column (PR #296); client-side sortable Status / Last checked (PR #292) | — | ✅ | — | ✅ Done | [Landing §3.1, §3.2b](/en/platform/tenant-migrations) |
| 9 | Apply dashboard views — fleet-table row action after Prisma deploy (`POST …/views/apply`, micro-data views step; 409 when already running; needs `tenant_migration.apply`) — new 2026-10-06 | ✅ | ✅ | ✅ | ✅ Done | [Landing §3.2c](/en/platform/tenant-migrations) |

### 27. Tenant Seed — `en/platform/tenant-seed/{lifecycle,ui-screens}.md`

New 2026-10-27 (Organization group, next to Tenant Migrations). Numbered 27 as an append-only ID; see the note under section 25.

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | Fleet summary card `SeedFleetSummary` (seeded / checkable counter, three-segment bar) | — | ✅ | — | ✅ Done | [UI §2.1](/en/platform/tenant-seed/ui-screens) |
| 2 | BU table with per-row **Check** / **Seed**, row statuses (Seeded / N missing / Not checked / No DB / Error), Missing-sets chips | ✅ | ✅ | ✅ | ✅ Done | [UI §2.3](/en/platform/tenant-seed/ui-screens), [Landing §3.1](/en/platform/tenant-seed) |
| 3 | Seed-set picker `SeedSetPickerDialog` (single-BU vs fleet mode; the eight ordered seed sets) | ✅ | ✅ | — | ✅ Done | [UI §2.5](/en/platform/tenant-seed/ui-screens), [Landing §1](/en/platform/tenant-seed) |
| 4 | **Seed all missing** — SPA-side sequential batch (no server-side all-BU endpoint), batch progress strip, **Check all** (4 in parallel) | — | ✅ | ✅ | ✅ Done | [UI §2.2, §2.4](/en/platform/tenant-seed/ui-screens), [Landing §3.3](/en/platform/tenant-seed) |
| 5 | CSV export (`tenant-seeds-YYYY-MM-DD.csv`) | — | ✅ | — | ✅ Done | [UI §2.2](/en/platform/tenant-seed/ui-screens) |
| 6 | Status check + seed stream lifecycle (connection resolution, NDJSON stream, idempotence, error handling, honest cancellation limits) | ✅ | — | — | ✅ Done | [Lifecycle §2–6](/en/platform/tenant-seed/lifecycle), [Landing §3.2](/en/platform/tenant-seed) |
| 7 | Gating — `TENANT_MIGRATION_API_ENABLED` kill switch, `x-deploy-token` CI path, `tenant_seed.read` / `.apply` (backstage-wide only), audit line | — | ✅ | ✅ | ✅ Done | [Landing §4](/en/platform/tenant-seed) |


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
| 1 | Explorer screen: columns/sorting (every data column since 2026-09-09 — backend whitelist of 8 keys), filters/search, CSV export | — | ✅ | ✅ | ✅ Done | [Landing §3](/en/platform/activity-events) |
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
| 9 | Worker-only job types `gl_run_due` and `pos_simphony_pull` (executed by `micro-cronjobs`, unknown to the console and gateway DTO) | ✅ | — | — | ✅ Done | [DM §3.7](/en/platform/cronjobs/data-model) |
| 10 | Skipped-run handling — `SkippedError` (micro-report `403 REPORT_TEMPLATE_UNAVAILABLE`) is logged and not retried | ✅ | — | — | ✅ Done | [DM §4.3](/en/platform/cronjobs/data-model) |

**Table A subtotal: 219 sub-processes, 219 Done, 0 Partial, 0 Not yet** (2026-10-27; was 175 on 2026-09-22 — the stale "167" here pre-dated that update).

## Table B — Landing-only modules (no sub-page folder)

### 21. Platform Migrations — `en/platform/platform-migrations.md`

| # | Sub-process | DM | UI | PERM | Status | Doc link |
|---|-------------|----|----|------|--------|----------|
| 1 | Status/Deploy card (`prisma migrate deploy` against the platform DB) | ✅ | ✅ | ✅ | ✅ Done | [§1, §3.3](/en/platform/platform-migrations) |
| 2 | Resolve-a-stuck-migration card | ✅ | ✅ | ✅ | ✅ Done | [§3.3](/en/platform/platform-migrations) |
| 3 | Seed data catalog (8 seed operations: `seed-application-api` added 2026-09-07, `seed-report-template-upload` dropped 2026-10-26 (`ad7499d87`); safety-to-rerun stated per op) | ✅ | ✅ | ✅ | ✅ Done | [§3.3](/en/platform/platform-migrations) |
| 4 | Drift check catalog (6 read-only incl. `check-application-api` + 1 hidden, writing check) | ✅ | ✅ | ✅ | ✅ Done | [§3.3](/en/platform/platform-migrations) |
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
| 7 | Current-BU persistence — `current_business_unit_id` on `tb_backstage_super_admin` (`setDefaultTenant`; added 2026-10-26, `5d7bab295`) | ✅ | — | — | ✅ Done | [§5.1](/en/platform/super-admins) |

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

**Table B subtotal: 27 sub-processes, 27 Done, 0 Partial, 0 Not yet** (2026-10-27; was 26).

## Table C — Standalone pages (not modules)

| Page | Sub-process | Page exists? | Content complete? | Status | Doc link |
|------|-------------|--------------|-------------------|--------|----------|
| Changelog | JSON source + authoring flow | ✅ | ✅ | ✅ Done | [Changelog §2](/en/platform/changelog) |
| Changelog | Public page + version badges | ✅ | ✅ | ✅ Done | [Changelog §3](/en/platform/changelog) |
| Changelog | Notable product removals (incl. Print Template Mapping) | ✅ | ✅ | ✅ Done | [Changelog §6](/en/platform/changelog) |
| Dashboard | Activity stream | ✅ | ✅ | ✅ Done | [Dashboard §2](/en/platform/dashboard) |
| Dashboard | Counts rail | ✅ | ✅ | ✅ Done | [Dashboard §3](/en/platform/dashboard) |
| Dashboard | What's not on the dashboard (scope boundary) | ✅ | ✅ | ✅ Done | [Dashboard §4](/en/platform/dashboard) |
| Dashboard | Return-to-page after sign-in (`/login?next=` from `PrivateRoute`, since 2026-10-26) | ✅ | ✅ | ✅ Done | [Dashboard §5](/en/platform/dashboard) |
| Landing | Page content + "Inside the Console" index | ✅ | ✅ | ✅ Done | [Landing §2–3](/en/platform/landing) |
| Landing | Confirmed drift: index vs. real sidebar | ✅ | ✅ | ✅ Done | [Landing §4](/en/platform/landing) |
| Landing | Roles/personas + gating (public route) | ✅ | ✅ | ✅ Done | [Landing §5](/en/platform/landing) |
| Profile | View/edit own identity, mounted at two routes | ✅ | ✅ | ✅ Done | [Profile §1](/en/platform/profile) |
| Profile | Change own password | ✅ | ✅ | ✅ Done | [Profile §3](/en/platform/profile) |
| Profile | Gating (authenticated-only) | ✅ | ✅ | ✅ Done | [Profile §4](/en/platform/profile) |
| Profile | Google sign-in return route `/login/callback` | ✅ | ✅ | ✅ Done | [Profile §3.1](/en/platform/profile) |
| Profile | `/403` Forbidden page | ✅ | ✅ | ✅ Done | [Profile §3.1](/en/platform/profile) |
| SQL Workbench | BU switcher + connection bar | ✅ | ✅ | ✅ Done | [§3](/en/platform/sql-workbench) |
| SQL Workbench | DB object tree (tables/views/procedures/functions) | ✅ | ✅ | ✅ Done | [§3](/en/platform/sql-workbench) |
| SQL Workbench | SQL editor + Run, destructive-statement confirmation | ✅ | ✅ | ✅ Done | [§3](/en/platform/sql-workbench) |
| SQL Workbench | Save (create/replace view/procedure/function) + Drop | ✅ | ✅ | ✅ Done | [§3](/en/platform/sql-workbench) |
| SQL Workbench | Result panel (virtual scroll, CSV export) | ✅ | ✅ | ✅ Done | [§3](/en/platform/sql-workbench) |
| SQL Workbench | Permission gate — read/manage split; 2026-08-20 backend gap closed | ✅ | ✅ | ✅ Done | [§4](/en/platform/sql-workbench) |

**Table C subtotal: 21 sub-processes, 21 Done, 0 Partial, 0 Not yet** (2026-10-27; was 18).

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
- **2026-10-27: the three new modules are EN-only.** `th/platform` still holds
  74 files; `ai-providers`, `dashboard-templates` and `tenant-seed` (landing +
  7 sub-pages, 10 files) have no TH counterpart, so the earlier "file-for-file
  identical" statement no longer holds. TH is deliberately deferred (see
  `.specs/resync-2026-10-27-progress.md`); existing TH pages were not re-synced
  to the backstage rename in this round.

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
- **2026-09-22 incremental update** (`.specs/resync-2026-09-22-progress.md`):
  not a re-enumeration — only the 20 SPA commits between `157a65e` and
  `f1c69f1` were diffed and folded in (interface-licence split, tenant-migration
  Resolve/Schema column, sortable headers, Landing Print-Mapping removal,
  `seed/check-application-api`, `interface_days`). Table A grew 167 → 175;
  total 211 → 219. The "19 of 74 files read in full" caveat from 2026-09-06
  still applies to every row this update did not touch.
- **2026-10-27 incremental update** (`.specs/resync-2026-10-27-progress.md`):
  not a re-enumeration — the delta between carmen-platform `f1c69f1` /
  backend `ef4d6f08f` and carmen-backstage `8405788f` / backend `c9d788829` was
  folded in, including the platform → backstage rename (backend `e0eaeff61`,
  SPA `318949a3`). Table A grew 175 → 219 (3 new modules + 24 rows on existing
  ones), B 26 → 27, C 18 → 21; total 219 → 267. Rule for next time: the new
  section numbers 25–27 are append-only IDs, placed at their Backstage-SPA nav
  position (Dashboard Templates after Report Templates, AI Providers after
  Feature Flags, Tenant Seed after Tenant Migrations); never renumber 1–24.
  Also refreshed the e2e column in "Source mapping" (the e2e suite now has
  smoke specs for six modules; the ones for Platform Migrations, Email
  Settings and Database Pools still use pre-rename `/platform/...` paths) — the
  routes/keys elsewhere in that table remain pre-rename spellings.
